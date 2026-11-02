"""Step 2 - decide a category, client, insurer and policy number for every file.

Pass 1 is keyword rules (free, instant). Words found in the file NAME count
most, then the email SUBJECT, then the document text and email body.
Pass 2 (optional) asks Claude about files the rules were unsure about.
Files corrected by hand (method = 'manual') are never changed again.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from . import db
from .config import Config, Named
from .textread import read_text

WEIGHTS = {"filename": 3, "subject": 2, "text": 1, "body": 1}

POLICY_RE = re.compile(
    r"\bpolicy\s*(?:no|number|num|#)?\.?\s*[:#\-]?\s*([A-Z0-9][A-Z0-9/\-]{5,30})",
    re.IGNORECASE,
)
# Replies/forwards carry the old thread underneath; only the newest part matters.
QUOTED_RE = re.compile(r"(?im)^\s*(?:from:|-----original message-----|on .{5,80} wrote:)")


@dataclass
class Result:
    category: str
    confidence: str          # high | medium | low
    scores: dict
    client: str
    insurer: str
    policy_no: str


def normalise(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[_\-.+()\[\],;:/\\]+", " ", text)
    return " " + " ".join(text.split()) + " "


def strip_quoted(body: str) -> str:
    m = QUOTED_RE.search(body or "")
    return body[: m.start()] if m else (body or "")


def _has(text: str, phrase: str) -> bool:
    return f" {normalise(phrase).strip()} " in text


class Classifier:
    def __init__(self, cfg: Config):
        self.cfg = cfg

    # ----- category ---------------------------------------------------
    def score(self, fields: dict[str, str]) -> dict[str, int]:
        norm = {k: normalise(v) for k, v in fields.items()}
        everything = " ".join(norm.values())
        scores = {}
        for cat in self.cfg.categories:
            texts = norm
            if cat.ignore:
                texts = {}
                for k, v in norm.items():
                    for phrase in cat.ignore:
                        v = v.replace(f" {normalise(phrase).strip()} ", " ")
                    texts[k] = v
            if cat.requires and not any(_has(everything, r) for r in cat.requires):
                scores[cat.name] = 0
                continue
            total = 0
            for field, text in texts.items():
                if any(_has(text, kw) for kw in cat.keywords):
                    total += WEIGHTS[field]
            scores[cat.name] = total
        return scores

    def pick(self, scores: dict[str, int]) -> tuple[str, str]:
        order = [c.name for c in self.cfg.categories]
        ranked = sorted(order, key=lambda n: (-scores.get(n, 0), order.index(n)))
        best = ranked[0]
        top = scores.get(best, 0)
        second = scores.get(ranked[1], 0) if len(ranked) > 1 else 0
        if top == 0:
            return self.cfg.fallback_category, "low"
        if top >= 3 and top >= second + 2:
            return best, "high"
        return best, "medium"

    # ----- client / insurer / policy ---------------------------------
    @staticmethod
    def _match(named: list[Named], haystack: str) -> str:
        for n in named:
            for m in n.match:
                if m in haystack:
                    return n.name
        return ""

    def insurer(self, addresses: str, text: str) -> str:
        return self._match(self.cfg.insurers, addresses.lower()) or \
            self._match(self.cfg.insurers, " ".join(text.lower().split()))

    def client(self, sender_name: str, sender_email: str, recipients: str, text: str) -> str:
        found = self._match(self.cfg.clients, f"{sender_email};{recipients}".lower()) or \
            self._match(self.cfg.clients, " ".join(text.lower().split()))
        if found:
            return found
        # The sender first, then whoever was on To/CC - skipping our own staff
        # and insurer addresses, so a mail from an insurer to us + the client
        # still finds the client.
        candidates = [sender_email] + [r for r in recipients.split(";") if r]
        for addr in candidates:
            domain = addr.rsplit("@", 1)[-1] if "@" in addr else ""
            if not domain or domain in self.cfg.own_domains:
                continue
            if self._match(self.cfg.insurers, addr):
                continue
            if domain in self.cfg.free_mail_domains:
                if addr == sender_email and sender_name and "@" not in sender_name:
                    return sender_name.strip().title()
                local = addr.split("@", 1)[0]
                if re.fullmatch(r"[a-z]+[._][a-z]+", local):   # rahul.mehta@gmail.com
                    return re.sub(r"[._]", " ", local).title()
                continue
            return domain_to_name(domain)
        return ""

    @staticmethod
    def policy_no(*texts: str) -> str:
        for t in texts:
            for m in POLICY_RE.finditer(t or ""):
                cand = m.group(1).strip("-/")
                if any(ch.isdigit() for ch in cand) and len(cand) >= 6:
                    return cand.upper()
        return ""

    def classify(self, row) -> Result:
        body = strip_quoted(row["body"] or "")
        text = row["text"] or ""
        fields = {
            "filename": row["filename"] or "",
            "subject": row["subject"] or "",
            "text": text,
            "body": body,
        }
        scores = self.score(fields)
        category, confidence = self.pick(scores)
        addresses = f"{row['sender_email']};{row['recipients']}"
        all_text = f"{row['subject']} {row['filename']} {text} {body}"
        return Result(
            category=category,
            confidence=confidence,
            scores=scores,
            client=self.client(row["sender_name"] or "", row["sender_email"] or "",
                               row["recipients"] or "", f"{row['subject']} {row['filename']} {text}"),
            insurer=self.insurer(addresses, all_text),
            policy_no=self.policy_no(row["filename"], row["subject"], text, body),
        )


GENERIC_SUBDOMAINS = {"in", "co", "com", "org", "net", "info", "biz", "ltd", "gov", "edu"}


def domain_to_name(domain: str) -> str:
    """abc-pharma.co.in -> 'Abc Pharma'."""
    parts = [p for p in domain.split(".") if p]
    # drop TLD-ish tail (co.in, com, in, org.in, ...)
    while len(parts) > 1 and (len(parts[-1]) == 2 or parts[-1] in GENERIC_SUBDOMAINS):
        parts.pop()
    core = parts[-1] if parts else domain
    return core.replace("-", " ").replace("_", " ").title()


def classify_all(cfg: Config, use_ai: bool = False, redo: bool = False) -> None:
    conn = db.connect(cfg.db_path)
    clf = Classifier(cfg)

    # 1) read document text once (cached in the database)
    pending = conn.execute(
        "SELECT sha256, ext, COALESCE(organized_path, '') AS op, store_path FROM files WHERE text IS NULL"
    ).fetchall()
    if pending:
        print(f"Reading text from {len(pending):,} documents...")
    for i, r in enumerate(pending, 1):
        path = cfg.output_dir / r["op"] if r["op"] else Path(r["store_path"])
        conn.execute("UPDATE files SET text=? WHERE sha256=?", (read_text(path, r["ext"]), r["sha256"]))
        if i % 200 == 0:
            conn.commit()
            print(f"   {i:,}/{len(pending):,}", flush=True)
    conn.commit()

    # 2) keyword rules
    where = "WHERE COALESCE(f.method,'') != 'manual'"
    if not redo:
        where += " AND f.category IS NULL"
    rows = db.first_message_for_files(conn, where).fetchall()
    print(f"Sorting {len(rows):,} files with keyword rules...")
    counts: dict[str, int] = {}
    for r in rows:
        res = clf.classify(r)
        counts[res.category] = counts.get(res.category, 0) + 1
        top = sorted(res.scores.items(), key=lambda kv: -kv[1])[:3]
        reason = "keywords: " + ", ".join(f"{k}={v}" for k, v in top if v) if res.scores else ""
        conn.execute(
            """UPDATE files SET category=?, confidence=?, method='rules', client=?, insurer=?,
               policy_no=?, reason=? WHERE sha256=?""",
            (res.category, res.confidence, res.client, res.insurer, res.policy_no,
             reason, r["sha256"]),
        )
    conn.commit()
    for name in cfg.category_names:
        if counts.get(name):
            print(f"   {name:<28} {counts[name]:>8,}")

    # 3) optional AI pass for the unsure ones
    if use_ai:
        from .ai import ai_pass
        ai_pass(cfg, conn)

    n_review = conn.execute(
        "SELECT COUNT(*) FROM files WHERE confidence='low' OR category=?", (cfg.fallback_category,)
    ).fetchone()[0]
    print(f"Files needing a human look: {n_review:,}")
