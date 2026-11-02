"""Optional pass 2 - ask an AI model (OpenAI or Claude) about files the keyword rules were unsure about.

Only a small, masked excerpt is sent: file name, email subject, sender's
company domain and the first part of the document text. PAN and Aadhaar
numbers are masked before anything leaves the PC. Files the rules already
sorted with high confidence, and KYC files, are never sent.
"""
from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel

from . import db
from .classify import strip_quoted
from .config import Config

PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
AADHAAR_RE = re.compile(r"\b\d{4}[ -]\d{4}[ -]\d{4}\b")
EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+91[ -]?)?[6-9]\d{9}(?!\d)")


class Verdict(BaseModel):
    category: str
    client: str
    insurer: str
    policy_no: str
    reason: str


def mask(text: str) -> str:
    text = PAN_RE.sub("[PAN]", text or "")
    text = AADHAAR_RE.sub("[AADHAAR]", text)
    text = EMAIL_RE.sub(lambda m: f"[email]@{m.group(2)}", text)
    return PHONE_RE.sub("[PHONE]", text)


def system_prompt(cfg: Config) -> str:
    cats = "\n".join(f"- {c.name}: {c.description}" for c in cfg.categories)
    return (
        "You sort email attachments for an Indian insurance broker (insurance intermediary). "
        "Given one attachment's file name, the email subject, the sender's company domain and "
        "an excerpt of the document, choose exactly one category from this list:\n"
        f"{cats}\n- {cfg.fallback_category}: use only if none of the above fits.\n\n"
        "Also extract, if present: the CLIENT (the insured company or person - never the "
        "insurer, TPA or the broker), the INSURER (insurance company), and the POLICY NUMBER. "
        "Use an empty string for anything not found. Do not guess. "
        "reason: one short sentence on why you chose the category."
    )


KEY_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}


def api_key(cfg: Config) -> str:
    """The key comes from the environment variable, or else from the key file
    (api-key.txt next to config.yaml). Never from config.yaml itself."""
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


def make_asker(cfg: Config, key: str):
    """Returns ask(system, content) -> Verdict | None for the configured provider."""
    if cfg.ai_provider == "openai":
        import openai
        client = openai.OpenAI(api_key=key, max_retries=5)

        def ask(system: str, content: str):
            resp = client.chat.completions.parse(
                model=cfg.ai_model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": content}],
                response_format=Verdict,
            )
            msg = resp.choices[0].message
            return None if msg.refusal else msg.parsed
        return ask

    import anthropic
    client = anthropic.Anthropic(api_key=key, max_retries=5)

    def ask(system: str, content: str):
        resp = client.messages.parse(
            model=cfg.ai_model,
            max_tokens=4000,
            system=system,
            messages=[{"role": "user", "content": content}],
            output_format=Verdict,
        )
        if resp.stop_reason == "refusal":
            return None
        return resp.parsed_output
    return ask


def ai_pass(cfg: Config, conn) -> None:
    key = api_key(cfg)
    if not key:
        print(f"AI step skipped: no API key. Paste your {cfg.ai_provider} key into "
              f"{cfg.ai_key_file} (see README, 'AI step').")
        return
    try:
        ask_model = make_asker(cfg, key)
    except ImportError:
        print(f"AI step skipped: run 1-setup.bat again to install the {cfg.ai_provider} package.")
        return

    rows = db.first_message_for_files(
        conn,
        "WHERE f.method = 'rules' AND f.confidence != 'high' AND f.category != 'KYC'",
    ).fetchall()
    if not rows:
        print("AI step: nothing to check - the rules were confident about every file.")
        return
    print(f"AI step: checking {len(rows):,} files with {cfg.ai_model} "
          f"({cfg.ai_workers} at a time)...")

    system = system_prompt(cfg)
    valid = {n.lower(): n for n in cfg.category_names}

    def ask(r):
        domain = (r["sender_email"] or "").rsplit("@", 1)[-1]
        content = (
            f"File name: {r['filename']}\n"
            f"Email subject: {mask(r['subject'] or '')}\n"
            f"Sender domain: {domain}\n"
            f"Email body (start): {mask(strip_quoted(r['body'] or '')[:600])}\n"
            f"Document text (start): {mask((r['text'] or '')[: cfg.ai_max_chars])}"
        )
        return r, ask_model(system, content)

    done = changed = failed = 0
    with ThreadPoolExecutor(max_workers=cfg.ai_workers) as pool:
        futures = [pool.submit(ask, r) for r in rows]
        for fut in as_completed(futures):
            try:
                r, v = fut.result()
            except Exception as exc:  # network / rate limit after retries / bad key
                failed += 1
                if failed <= 5:
                    print(f"   AI error: {exc}")
                if failed == 20 and done == 0:
                    print("AI step stopped: every request is failing. Check the API key, "
                          "the model name in config.yaml, and that the account has credit.")
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                continue
            done += 1
            if v is None:
                failed += 1
                continue
            cat = valid.get(v.category.strip().lower(), cfg.fallback_category)
            if cat != r["category"]:
                changed += 1
            conn.execute(
                """UPDATE files SET category=?, confidence=?, method='ai',
                   client=COALESCE(NULLIF(?, ''), client),
                   insurer=COALESCE(NULLIF(?, ''), insurer),
                   policy_no=COALESCE(NULLIF(?, ''), policy_no),
                   reason=? WHERE sha256=?""",
                (cat, "low" if cat == cfg.fallback_category else "medium",
                 v.client.strip(), v.insurer.strip(), v.policy_no.strip(),
                 "AI: " + v.reason.strip()[:300], r["sha256"]),
            )
            if done % 50 == 0:
                conn.commit()
                print(f"   {done:,}/{len(rows):,}", flush=True)
    conn.commit()
    print(f"AI step: {done:,} checked, {changed:,} moved to a different category, {failed} failed.")
