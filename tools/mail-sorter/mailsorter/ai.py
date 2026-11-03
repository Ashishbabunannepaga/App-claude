"""Optional pass 2 - an AI model reads each EMAIL as a whole and sorts its attachments.

For every email it sees: date, folder, subject, From, To, CC, whether it is a
forward, the newest message, the forwarded / quoted messages underneath (with
their own From/To/CC/date), and every attachment's name, type and opening text,
plus what the keyword rules guessed. One request covers all attachments of an
email, so nothing is read twice and nothing is missed.

Cost controls
  * scope 'unsure' sends only emails whose files the rules were unsure about;
    scope 'all' sends every email with attachments (most accurate).
  * Each email is analysed once (ai_status in the database) - re-runs cost nothing.
  * OpenAI Batch API (half price) for big runs; 'estimate' prints the cost first;
    the step refuses to start above ai.max_cost_usd.
  * provider 'local' runs a free model on this PC (Ollama) - no API cost at all.

Privacy: PAN, GSTIN, Aadhaar, phone numbers and the name part of email addresses are
masked before anything is sent. KYC documents' text is never sent.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from . import db
from .config import Config
from .parse import parse_body

PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
GSTIN_RE = re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]\b")   # contains the PAN
AADHAAR_RE = re.compile(r"\b\d{4}[ -]\d{4}[ -]\d{4}\b")
EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)")

KEY_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "local": ""}
CHARS_PER_TOKEN = 3.5            # conservative - real text is usually ~4
BATCH_MAX_REQUESTS = 40_000      # OpenAI allows 50,000 per batch
BATCH_MAX_BYTES = 150 * 1024 * 1024
OPEN_BATCH = ("validating", "in_progress", "finalizing", "cancelling")


class FileVerdict(BaseModel):
    file_id: str
    category: str
    policy_no: str
    reason: str


class EmailVerdict(BaseModel):
    email_category: str
    summary: str
    client: str
    insurer: str
    policy_no: str
    files: list[FileVerdict]


# ---------------------------------------------------------------- helpers
def mask(text: str) -> str:
    text = GSTIN_RE.sub("[GSTIN]", text or "")
    text = PAN_RE.sub("[PAN]", text)
    text = AADHAAR_RE.sub("[AADHAAR]", text)
    text = EMAIL_RE.sub(lambda m: f"[email]@{m.group(2)}", text)
    return PHONE_RE.sub("[PHONE]", text)


def _cut(text: str, n: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n] + " [...]"


def api_key(cfg: Config) -> str:
    """The key comes from the environment variable, or else from the key file
    (api-key.txt next to config.yaml). Never from config.yaml itself."""
    if cfg.ai_provider == "local":
        return "local"
    key = os.environ.get(KEY_ENV[cfg.ai_provider], "").strip()
    if key:
        return key
    path = cfg.ai_key_file
    if path and path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                return line
    return ""


def system_prompt(cfg: Config) -> str:
    cats = "\n".join(f"- {c.name}: {c.description}" for c in cfg.categories)
    return (
        "You are an expert operations assistant at an Indian insurance broker (insurance "
        "intermediary). You read one email at a time - its headers, the newest message, any "
        "forwarded or quoted messages underneath, and its attachments - and sort it.\n\n"
        f"Categories:\n{cats}\n- {cfg.fallback_category}: only if nothing above fits.\n\n"
        "Rules:\n"
        "1. Give every attachment (F1, F2, ...) exactly one category. Judge each file on its own "
        "name and text, using the email for context: one email can carry a claim form AND a KYC "
        "document.\n"
        "2. In a forward, the forwarded message is the real content; the newest part is often "
        "just 'FYI' or 'please process'.\n"
        "3. Endorsements: adding members/lives/vehicles = Endorsement Addition; removing = "
        "Endorsement Deletion; corrections or endorsement copies = Endorsement Other.\n"
        "4. 'Keyword rules guessed' is a hint from simple word matching - overrule it when the "
        "content says otherwise.\n"
        "5. client = the insured company or person (never the insurer, TPA, surveyor or our own "
        "broking firm). insurer = the insurance company. policy_no = the policy number exactly "
        "as written. Use \"\" for anything not clearly stated - never guess.\n"
        "6. email_category = what the email as a whole is about (same category list). "
        "summary = one short factual line (who wants what), max 20 words.\n"
        "7. reason = a few words on why that file got its category.\n"
        "Reply with JSON only."
    )


def response_schema(cfg: Config) -> dict:
    cats = cfg.category_names
    file_props = {
        "file_id": {"type": "string"},
        "category": {"type": "string", "enum": cats},
        "policy_no": {"type": "string"},
        "reason": {"type": "string"},
    }
    props = {
        "email_category": {"type": "string", "enum": cats},
        "summary": {"type": "string"},
        "client": {"type": "string"},
        "insurer": {"type": "string"},
        "policy_no": {"type": "string"},
        "files": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": list(file_props), "properties": file_props}},
    }
    return {"type": "object", "additionalProperties": False, "required": list(props),
            "properties": props}


# ---------------------------------------------------------------- what to send
def pending_emails(cfg: Config, conn, scope: str | None = None) -> "OrderedDict[str, list]":
    """Emails still to analyse -> the files (first seen in that email) to judge."""
    scope = scope or cfg.ai_scope
    where = "WHERE f.method = 'rules'"
    if scope == "unsure":
        where += " AND f.confidence != 'high' AND f.category != 'KYC'"
    rows = db.first_message_for_files(conn, where).fetchall()
    status = {r[0]: r[1] for r in conn.execute("SELECT entry_id, ai_status FROM messages")}
    out: OrderedDict[str, list] = OrderedDict()
    for r in rows:
        if status.get(r["entry_id"]) in ("queued", "done"):
            continue
        out.setdefault(r["entry_id"], []).append(r)
    return out


def email_prompt(cfg: Config, conn, files: list) -> str:
    m = conn.execute("SELECT * FROM messages WHERE entry_id=?", (files[0]["entry_id"],)).fetchone()
    parsed = parse_body(m["body"] or "", m["subject"] or "")
    budget = cfg.ai_max_chars
    body_budget = int(budget * 0.55)

    out = [
        "EMAIL",
        f"Date: {(m['received'] or '')[:16]}   Folder: {m['folder']}",
        f"Subject: {mask(m['subject'] or '')}",
        f"From: {mask(m['sender_name'] or '')} <{mask(m['sender_email'] or '')}>",
        f"To: {mask((m['to_addrs'] or m['recipients'] or '').replace(';', ', '))}",
        f"CC: {mask((m['cc_addrs'] or '').replace(';', ', ')) or '-'}",
    ]
    if parsed.is_forward:
        out.append("This email is a FORWARD of an earlier message.")
    newest = _cut(mask(parsed.newest), min(2500, body_budget))
    out += ["", "NEWEST MESSAGE:", newest or "(empty)"]
    used = len(newest)
    parts = sorted(parsed.parts, key=lambda p: p.kind != "forwarded")   # forwarded content first
    for i, p in enumerate(parts, 1):
        room = body_budget - used
        if room < 200:
            out.append(f"[{len(parts) - i + 1} older message(s) not shown]")
            break
        text = _cut(mask(p.body), min(1500, room))
        used += len(text)
        out += ["", f"--- {p.kind.upper()} MESSAGE {i}: from {mask(p.sender)} | date {p.date} | "
                    f"to {mask(p.to)} | cc {mask(p.cc) or '-'} | subject {mask(p.subject)} ---", text]

    sent_names = {f["filename"] for f in files}
    others = [r[0] for r in conn.execute(
        "SELECT filename FROM attachments WHERE entry_id=? ORDER BY id", (m["entry_id"],))
        if r[0] not in sent_names]
    per_file = max(300, min(1500, (budget - used) // max(1, len(files))))
    out += ["", f"ATTACHMENTS TO SORT ({len(files)}):"]
    for i, f in enumerate(files, 1):
        kb = round((f["size"] or 0) / 1024)
        out.append(f"[F{i}] {f['filename']} ({(f['ext'] or '').lstrip('.').upper() or '?'}, {kb} KB) "
                   f"- keyword rules guessed: {f['category']} ({f['confidence']})")
        if f["category"] == "KYC":
            out.append("    text: (identity/KYC document - text not sent)")
        elif f["text"]:
            out.append("    text: " + _cut(mask(f["text"]), per_file))
        else:
            out.append("    text: (no readable text - scanned image or unsupported type)")
    if others:
        out.append("Other attachments in this email (already sorted): " + ", ".join(others[:15]))
    return "\n".join(out)


def _chat_body(cfg: Config, content: str) -> dict:
    return {
        "model": cfg.ai_model,
        "messages": [{"role": "system", "content": system_prompt(cfg)},
                     {"role": "user", "content": content}],
        "response_format": {"type": "json_schema", "json_schema": {
            "name": "email_verdict", "strict": True, "schema": response_schema(cfg)}},
    }


# ---------------------------------------------------------------- cost estimate
def estimate(cfg: Config, conn, scope: str | None = None) -> dict:
    emails = pending_emails(cfg, conn, scope)
    sys_chars = len(system_prompt(cfg)) + len(json.dumps(response_schema(cfg)))
    in_chars = out_tok = n_files = 0
    for files in emails.values():
        in_chars += sys_chars + len(email_prompt(cfg, conn, files))
        out_tok += 70 + 45 * len(files)
        n_files += len(files)
    in_tok = in_chars / CHARS_PER_TOKEN
    live = 0.0 if cfg.ai_provider == "local" else \
        (in_tok * cfg.ai_price_in + out_tok * cfg.ai_price_out) / 1e6
    return {"emails": len(emails), "files": n_files, "input_tokens": int(in_tok),
            "output_tokens": int(out_tok), "cost_live": live, "cost_batch": live / 2}


def _usd(x: float) -> str:
    return f"${x:,.2f}" if x >= 1 else f"${x:.4f}"


def print_estimate(cfg: Config, conn, scope: str | None = None) -> dict:
    e = estimate(cfg, conn, scope)
    print(f"AI estimate ({cfg.ai_provider} / {cfg.ai_model}, scope '{scope or cfg.ai_scope}'):")
    print(f"   emails to read:   {e['emails']:,}  (covering {e['files']:,} files)")
    print(f"   tokens:           ~{e['input_tokens']:,} in / ~{e['output_tokens']:,} out")
    if cfg.ai_provider == "local":
        print("   cost:             free (runs on this PC)")
    else:
        print(f"   cost one-by-one:  ~{_usd(e['cost_live'])}   (about Rs {e['cost_live'] * 85:,.0f})")
        if cfg.ai_provider == "openai":
            print(f"   cost as a batch:  ~{_usd(e['cost_batch'])}   (about Rs {e['cost_batch'] * 85:,.0f})")
        print(f"   (prices from config.yaml: ${cfg.ai_price_in}/M in, ${cfg.ai_price_out}/M out "
              "- check your provider's pricing page)")
    return e


# ---------------------------------------------------------------- applying results
def apply_verdict(cfg: Config, conn, entry_id: str, verdict: "EmailVerdict", shas: list[str]) -> int:
    """Writes one email's AI answer into the database. Returns files that changed category."""
    valid = {n.lower(): n for n in cfg.category_names}
    by_id = {fv.file_id.strip().upper(): fv for fv in verdict.files}
    changed = 0
    for i, sha in enumerate(shas, 1):
        fv = by_id.get(f"F{i}")
        if fv is None:
            continue
        cat = valid.get(fv.category.strip().lower(), cfg.fallback_category)
        row = conn.execute("SELECT category, method FROM files WHERE sha256=?", (sha,)).fetchone()
        if row is None or row["method"] in ("manual", "ai"):
            continue
        if cat == cfg.fallback_category:
            conf = "low"
        elif cat == row["category"]:
            conf = "high"          # rules and AI agree
        else:
            conf = "medium"
            changed += 1
        reason = f"AI: {fv.reason.strip()[:250]}"
        if cat != row["category"]:
            reason += f" (rules said {row['category']})"
        conn.execute(
            """UPDATE files SET category=?, confidence=?, method='ai',
               client=COALESCE(NULLIF(?, ''), client), insurer=COALESCE(NULLIF(?, ''), insurer),
               policy_no=COALESCE(NULLIF(?, ''), NULLIF(?, ''), policy_no), reason=?
               WHERE sha256=?""",
            (cat, conf, verdict.client.strip(), verdict.insurer.strip(), fv.policy_no.strip(),
             verdict.policy_no.strip(), reason, sha))
    conn.execute(
        "UPDATE messages SET ai_status='done', email_category=?, summary=? WHERE entry_id=?",
        (valid.get(verdict.email_category.strip().lower(), cfg.fallback_category),
         verdict.summary.strip()[:300], entry_id))
    return changed


def _parse_content(content: str) -> "EmailVerdict | None":
    if not content:
        return None
    try:
        return EmailVerdict.model_validate_json(content)
    except Exception:
        m = re.search(r"\{.*\}", content, re.S)       # local models sometimes add prose
        try:
            return EmailVerdict.model_validate_json(m.group(0)) if m else None
        except Exception:
            return None


# ---------------------------------------------------------------- live mode
def _openai_client(cfg: Config, key: str):
    import openai
    kwargs = {"api_key": key, "max_retries": 5}
    if cfg.ai_provider == "local":
        kwargs["base_url"] = cfg.ai_base_url or "http://localhost:11434/v1"
        kwargs["timeout"] = 600
    elif cfg.ai_base_url:
        kwargs["base_url"] = cfg.ai_base_url
    return openai.OpenAI(**kwargs)


def make_asker(cfg: Config, key: str):
    """Returns ask(content) -> EmailVerdict | None."""
    if cfg.ai_provider in ("openai", "local"):
        client = _openai_client(cfg, key)

        def ask(content: str):
            resp = client.chat.completions.create(**_chat_body(cfg, content))
            msg = resp.choices[0].message
            if getattr(msg, "refusal", None):
                return None
            return _parse_content(msg.content)
        return ask

    import anthropic
    client = anthropic.Anthropic(api_key=key, max_retries=5)

    def ask(content: str):
        resp = client.messages.parse(
            model=cfg.ai_model, max_tokens=4000, system=system_prompt(cfg),
            messages=[{"role": "user", "content": content}], output_format=EmailVerdict)
        if resp.stop_reason == "refusal":
            return None
        return resp.parsed_output
    return ask


def run_live(cfg: Config, conn, emails: "OrderedDict[str, list]", key: str) -> None:
    ask_model = make_asker(cfg, key)
    jobs = [(eid, files, email_prompt(cfg, conn, files)) for eid, files in emails.items()]
    workers = 1 if cfg.ai_provider == "local" else cfg.ai_workers
    print(f"AI step: reading {len(jobs):,} emails with {cfg.ai_model} ({workers} at a time)...")
    done = changed = failed = 0
    started = time.time()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(ask_model, content): (eid, files) for eid, files, content in jobs}
        for fut in as_completed(futures):
            eid, files = futures[fut]
            try:
                v = fut.result()
            except Exception as exc:  # network / rate limit after retries / bad key / bad model
                failed += 1
                if failed <= 5:
                    print(f"   AI error: {exc}")
                if failed >= 20 and done == 0:
                    print("AI step stopped: every request is failing. Check the API key, the model "
                          "name in config.yaml, and that the account has credit.")
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                continue
            if v is None:
                failed += 1
                conn.execute("UPDATE messages SET ai_status='failed' WHERE entry_id=?", (eid,))
                continue
            done += 1
            changed += apply_verdict(cfg, conn, eid, v, [f["sha256"] for f in files])
            if done % 50 == 0:
                conn.commit()
                rate = done / max(1e-6, time.time() - started)
                left = (len(jobs) - done - failed) / max(rate, 1e-6) / 60
                print(f"   {done:,}/{len(jobs):,} emails  (~{left:.0f} min left)", flush=True)
    conn.commit()
    print(f"AI step: {done:,} emails read, {changed:,} files moved to a better category, "
          f"{failed} failed (retried next run).")


# ---------------------------------------------------------------- batch mode (OpenAI)
def submit_batches(cfg: Config, conn, emails: "OrderedDict[str, list]", client) -> list[str]:
    rowid = {r[0]: r[1] for r in conn.execute("SELECT entry_id, rowid FROM messages")}
    tmp_dir = cfg.work_dir / "batches"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    chunks, lines, size = [], [], 0
    for eid, files in emails.items():
        line = json.dumps({"custom_id": f"m{rowid[eid]}", "method": "POST",
                           "url": "/v1/chat/completions",
                           "body": _chat_body(cfg, email_prompt(cfg, conn, files))},
                          ensure_ascii=False)
        n_bytes = len(line.encode("utf-8")) + 1
        if lines and (len(lines) >= BATCH_MAX_REQUESTS or size + n_bytes > BATCH_MAX_BYTES):
            chunks.append(lines)
            lines, size = [], 0
        lines.append((eid, [f["sha256"] for f in files], line))
        size += n_bytes
    if lines:
        chunks.append(lines)

    ids = []
    for chunk in chunks:
        fd, name = tempfile.mkstemp(suffix=".jsonl", dir=tmp_dir)
        os.close(fd)
        path = Path(name)
        path.write_text("\n".join(x[2] for x in chunk) + "\n", encoding="utf-8")
        with open(path, "rb") as fh:
            up = client.files.create(file=fh, purpose="batch")
        batch = client.batches.create(input_file_id=up.id, endpoint="/v1/chat/completions",
                                      completion_window="24h")
        conn.execute("INSERT OR REPLACE INTO ai_batches VALUES (?,?,?,?)",
                     (batch.id, batch.status, len(chunk), datetime.now().isoformat(timespec="seconds")))
        conn.executemany("UPDATE messages SET ai_status='queued', ai_batch=?, ai_files=? WHERE entry_id=?",
                         [(batch.id, json.dumps(shas), eid) for eid, shas, _ in chunk])
        conn.commit()
        path.unlink(missing_ok=True)
        ids.append(batch.id)
        print(f"   submitted batch {batch.id} with {len(chunk):,} emails")
    return ids


def _file_text(client, file_id: str) -> str:
    content = client.files.content(file_id)
    return content.text if hasattr(content, "text") else content.read().decode("utf-8")


def collect_batch(cfg: Config, conn, client, batch) -> tuple[int, int]:
    by_rowid = {f"m{r[0]}": (r[1], r[2]) for r in conn.execute(
        "SELECT rowid, entry_id, ai_files FROM messages WHERE ai_batch=?", (batch.id,))}
    done = failed = 0
    for fid in (getattr(batch, "output_file_id", None), getattr(batch, "error_file_id", None)):
        if not fid:
            continue
        for raw in _file_text(client, fid).splitlines():
            if not raw.strip():
                continue
            item = json.loads(raw)
            eid, shas = by_rowid.get(item.get("custom_id"), (None, None))
            if eid is None:
                continue
            verdict = None
            resp = item.get("response") or {}
            if resp.get("status_code") == 200:
                msg = resp["body"]["choices"][0]["message"]
                if not msg.get("refusal"):
                    verdict = _parse_content(msg.get("content") or "")
            if verdict is None:
                failed += 1
                conn.execute("UPDATE messages SET ai_status='failed' WHERE entry_id=?", (eid,))
            else:
                done += 1
                apply_verdict(cfg, conn, eid, verdict, json.loads(shas or "[]"))
    # anything the batch never answered goes back in the queue
    conn.execute("UPDATE messages SET ai_status=NULL WHERE ai_batch=? AND ai_status='queued'", (batch.id,))
    conn.commit()
    return done, failed


def wait_for_batches(cfg: Config, conn, client, poll_seconds: int = 60) -> None:
    """Polls submitted batches until all are finished, collecting each as it completes.
    Safe to interrupt: the batch ids are in the database and the next run resumes."""
    while True:
        open_ids = [r[0] for r in conn.execute(
            f"SELECT batch_id FROM ai_batches WHERE status IN ({','.join('?' * len(OPEN_BATCH))})",
            OPEN_BATCH)]
        if not open_ids:
            return
        still_open = 0
        for bid in open_ids:
            b = client.batches.retrieve(bid)
            rc = getattr(b, "request_counts", None)
            prog = f"({rc.completed:,}/{rc.total:,} done)" if rc and getattr(rc, "total", 0) else ""
            print(f"   batch {bid}: {b.status} {prog}", flush=True)
            if b.status in OPEN_BATCH:
                still_open += 1
                conn.execute("UPDATE ai_batches SET status=? WHERE batch_id=?", (b.status, bid))
            else:   # completed / failed / expired / cancelled
                done, failed = collect_batch(cfg, conn, client, b)
                conn.execute("UPDATE ai_batches SET status=? WHERE batch_id=?", (b.status, bid))
                print(f"   batch {bid}: {done:,} emails sorted, {failed} failed (retried next run)")
            conn.commit()
        if still_open:
            print("   waiting for OpenAI (usually 1-6 hours, at most 24). It is safe to close this "
                  "window - running again picks the results up.", flush=True)
            time.sleep(poll_seconds)


# ---------------------------------------------------------------- entry point
def ai_pass(cfg: Config, conn, poll_seconds: int = 60) -> None:
    key = api_key(cfg)
    if not key:
        print(f"AI step skipped: no API key. Paste your {cfg.ai_provider} key into "
              f"{cfg.ai_key_file} (see README, 'AI step').")
        return
    try:
        if cfg.ai_provider == "anthropic":
            import anthropic  # noqa: F401
        else:
            import openai  # noqa: F401
    except ImportError:
        print("AI step skipped: run 1-setup.bat again to install the AI package.")
        return

    use_batch = cfg.ai_provider == "openai" and cfg.ai_batch != "never"
    client = _openai_client(cfg, key) if use_batch else None
    if use_batch:
        wait_for_batches(cfg, conn, client, poll_seconds)        # results from an earlier run

    conn.execute("UPDATE messages SET ai_status=NULL WHERE ai_status='failed'")   # one more go
    emails = pending_emails(cfg, conn)
    if not emails:
        print("AI step: nothing new to read.")
        return
    est = print_estimate(cfg, conn)
    batch_now = use_batch and (cfg.ai_batch == "always" or len(emails) >= cfg.ai_batch_min_emails)
    cost = est["cost_batch"] if batch_now else est["cost_live"]
    if cost > cfg.ai_max_cost_usd:
        print(f"AI step NOT started: estimated {_usd(cost)} is above  max_cost_usd: "
              f"{cfg.ai_max_cost_usd}  in config.yaml. Raise that limit if the cost is OK.")
        return
    if batch_now:
        print(f"AI step: sending {len(emails):,} emails to OpenAI as a batch (half price)...")
        submit_batches(cfg, conn, emails, client)
        wait_for_batches(cfg, conn, client, poll_seconds)
    else:
        run_live(cfg, conn, emails, key)
