"""Run with:  python -m pytest tests  (from tools/mail-sorter)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
import yaml
from openpyxl import load_workbook

from mailsorter import db
from mailsorter.ai import mask
from mailsorter.classify import Classifier, classify_all, domain_to_name, strip_quoted
from mailsorter.config import load_config
from mailsorter.demo import make_demo
from mailsorter.organize import fiscal_year, organize, safe, target_relpath
from mailsorter.report import EXCEL_NAME, ID_COL, import_review, report

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def cfg(tmp_path):
    raw = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    raw["paths"] = {"work_dir": str(tmp_path / "work"), "store_dir": str(tmp_path / "work" / "store"),
                    "output_dir": str(tmp_path / "out")}
    p = tmp_path / "config.yaml"
    p.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return load_config(p)


def row(**kw):
    base = dict(filename="", subject="", text="", body="", sender_name="", sender_email="",
                recipients="")
    base.update(kw)
    return base


@pytest.mark.parametrize("filename,subject,expected", [
    ("Addition_list_Mar.xlsx", "Member addition in GMC", "Endorsement Addition"),
    ("Deletion_list.xlsx", "Deletion endorsement for employees", "Endorsement Deletion"),
    ("Endt_copy.pdf", "Endorsement copy", "Endorsement Other"),
    ("Claim_form.pdf", "Claim intimation - hospitalisation", "Claims"),
    ("Discharge_summary.pdf", "Cashless request", "Claims"),
    ("Quotation_ICICI.pdf", "Quote for fire policy", "Quotes"),
    ("Renewal_notice.pdf", "Policy due for renewal", "Renewals"),
    ("Policy_schedule.pdf", "Policy issued", "Policy Copies"),
    ("Payment_proof.pdf", "Please book the policy", "Booking"),
    ("PAN_card.pdf", "KYC documents", "KYC"),
    ("Tax_Invoice_123.pdf", "Brokerage invoice", "Invoices & CD"),
    ("CD_statement.xlsx", "CD statement as on date", "Invoices & CD"),
    ("scan0001.pdf", "Fwd: docs", "Other - Needs Review"),
])
def test_categories(cfg, filename, subject, expected):
    res = Classifier(cfg).classify(row(filename=filename, subject=subject))
    assert res.category == expected


def test_no_claim_bonus_is_not_a_claim(cfg):
    res = Classifier(cfg).classify(row(filename="Renewal_terms.pdf", subject="Renewal",
                                       text="No claim bonus 20% applicable. NCB retained."))
    assert res.category == "Renewals"


def test_addition_needs_context(cfg):
    # "in addition" in an unrelated mail must not become an endorsement
    res = Classifier(cfg).classify(row(filename="minutes.pdf", subject="Meeting",
                                       body="In addition, please share the brochure"))
    assert res.category != "Endorsement Addition"


def test_extracts_client_insurer_policy(cfg):
    c = Classifier(cfg)
    res = c.classify(row(filename="Policy_schedule.pdf", subject="Policy issued",
                         text="Policy No: 4016/X/123456/00/000 issued",
                         sender_email="ops@hdfcergo.com",
                         recipients="ops@capitupindia.com;hr@sunrise-pharma.co.in"))
    assert res.insurer == "HDFC ERGO"
    assert res.client == "Sunrise Pharma"
    assert res.policy_no == "4016/X/123456/00/000"


def test_configured_client_wins(cfg):
    from mailsorter.config import Named
    cfg.clients = [Named("Sunrise Pharma Ltd", ["sunrise-pharma"])]
    res = Classifier(cfg).classify(row(sender_email="hr@sunrise-pharma.co.in"))
    assert res.client == "Sunrise Pharma Ltd"


def test_helpers():
    assert domain_to_name("abc-pharma.co.in") == "Abc Pharma"
    assert domain_to_name("mail.xyz.com") == "Xyz"
    assert fiscal_year(__import__("datetime").datetime(2026, 3, 31)) == "FY2025-26"
    assert fiscal_year(__import__("datetime").datetime(2026, 4, 1)) == "FY2026-27"
    assert safe('a<b>:c"d/e\\f|g?h*') == "a b c d e f g h"
    assert safe("CON") == "_CON"
    assert strip_quoted("new text\nFrom: old\nclaim") == "new text\n"
    masked = mask("PAN ABCDE1234F aadhaar 1234 5678 9012 call 9876543210 a.b@x.com GSTIN 27ABCDE1234F1Z5")
    assert "ABCDE1234F" not in masked and "1234 5678 9012" not in masked
    assert "9876543210" not in masked and "a.b@" not in masked


def test_long_paths_are_trimmed(cfg):
    r = dict(received="2025-05-01T10:00:00", category="Claims", client="C" * 200, insurer="",
             policy_no="", filename="x" * 300 + ".pdf", ext=".pdf")
    rel = target_relpath(r, cfg)
    assert len(str(cfg.output_dir / rel)) <= 255
    assert rel.suffix == ".pdf"


def test_full_pipeline_and_review_roundtrip(cfg):
    make_demo(cfg, n_emails=120)
    classify_all(cfg)
    organize(cfg)
    report(cfg)

    conn = sqlite3.connect(cfg.db_path)
    n_files, n_placed = conn.execute(
        "SELECT COUNT(*), COUNT(organized_path) FROM files").fetchone()
    assert n_files > 0 and n_files == n_placed
    for (rel,) in conn.execute("SELECT organized_path FROM files"):
        assert (cfg.output_dir / rel).exists()
    assert (cfg.output_dir / "Dashboard.html").read_text(encoding="utf-8").count("/*__DATA__*/") == 0

    # Resumable: a second classify/organize run changes nothing
    classify_all(cfg)
    organize(cfg)
    assert conn.execute("SELECT COUNT(*) FROM files WHERE organized_path IS NULL").fetchone()[0] == 0

    # Correct one file in Excel -> import-review -> organize moves it
    xl = cfg.output_dir / EXCEL_NAME
    wb = load_workbook(xl)
    ws = wb["Index"]
    sha = ws.cell(row=2, column=ID_COL).value
    old = ws.cell(row=2, column=2).value
    new = "KYC" if old != "KYC" else "Claims"
    ws.cell(row=2, column=2).value = new
    wb.save(xl)
    import_review(cfg)
    organize(cfg)
    cat, method, rel = conn.execute(
        "SELECT category, method, organized_path FROM files WHERE sha256=?", (sha,)).fetchone()
    assert (cat, method) == (new, "manual")
    assert rel.startswith(new + "/") and (cfg.output_dir / rel).exists()

    # Manual corrections survive a full re-sort
    classify_all(cfg, redo=True)
    assert conn.execute("SELECT category FROM files WHERE sha256=?", (sha,)).fetchone()[0] == new


# ------------------------------------------------------------------ forwards / CC
def test_parse_gmail_and_outlook_forwards():
    from mailsorter.parse import parse_body
    g = parse_body("Please process.\n\n---------- Forwarded message ---------\n"
                   "From: HR <hr@sunrise.com>\nDate: Mon, 3 Jun 2024\nSubject: Addition\n"
                   "To: ops@capitupindia.com\nCc: fin@sunrise.com\n\nAdd these members.",
                   "Fwd: Addition")
    assert g.is_forward and g.newest == "Please process."
    assert (g.parts[0].kind, g.parts[0].sender_email, g.parts[0].cc) == ("forwarded", "hr@sunrise.com", "fin@sunrise.com")
    assert g.parts[0].body == "Add these members."
    assert g.original_sender({"capitupindia.com"}) == "hr@sunrise.com"

    o = parse_body("Noted.\n\nFrom: Ravi <ravi@tataaig.com>\nSent: Tuesday, 4 June 2024\n"
                   "To: ops@capitupindia.com\nSubject: RE: Claim\n\nSend discharge summary.\n\n"
                   "On Mon, 3 Jun 2024 at 10:15, HR <hr@sunrise.com> wrote:\n> docs attached",
                   "RE: Claim")
    assert not o.is_forward and o.newest == "Noted."
    assert [p.sender_email for p in o.parts] == ["ravi@tataaig.com", "hr@sunrise.com"]


def test_forward_finds_client_from_original_sender(cfg):
    """Our staff forwards the client's mail to the insurer: client = original sender."""
    body = ("Please process.\n\nFrom: HR <hr@kaveri-logistics.in>\nSent: Monday\n"
            "To: ops@capitupindia.com\nSubject: Claim intimation\n\nClaim docs attached.")
    res = Classifier(cfg).classify(row(filename="docs.pdf", subject="FW: Claim intimation", body=body,
                                       sender_email="ops@capitupindia.com",
                                       recipients="uw@tataaig.com"))
    assert res.client == "Kaveri Logistics"
    assert res.insurer == "Tata AIG"
    assert res.category == "Claims"


def test_to_cc_and_forward_reach_excel(cfg):
    make_demo(cfg, n_emails=120)
    classify_all(cfg)
    organize(cfg)
    report(cfg)
    conn = db.connect(cfg.db_path)
    assert conn.execute("SELECT COUNT(*) FROM messages WHERE is_forward=1 AND fwd_from != ''").fetchone()[0] > 0
    ws = load_workbook(cfg.output_dir / EXCEL_NAME, read_only=True)["Index"]
    head = [c.value for c in next(ws.iter_rows(max_row=1))]
    assert {"To", "CC", "Forwarded from", "Email summary (AI)"} <= set(head)
    fwd_col = head.index("Forwarded from")
    assert any(r[fwd_col] for r in ws.iter_rows(min_row=2, values_only=True))


# ------------------------------------------------------------------ AI step
def _verdict_json(n_files, category="Claims"):
    return json.dumps({
        "email_category": category, "summary": "Client sends claim documents",
        "client": "Sunrise Pharma", "insurer": "Tata AIG", "policy_no": "P-1",
        "files": [{"file_id": f"F{i}", "category": category, "policy_no": "", "reason": "claim form"}
                  for i in range(1, n_files + 1)]})


def _n_files(content: str) -> int:
    return content.count("\n[F")


class FakeOpenAI:
    """Stands in for openai.OpenAI: chat completions + files + batches."""
    def __init__(self, **kw):
        import types
        self.kw = kw
        self.sent = []
        self.batches_made = {}
        outer = self

        class Completions:
            def create(self, **body):
                assert body["response_format"]["json_schema"]["strict"] is True
                content = body["messages"][1]["content"]
                outer.sent.append(content)
                msg = types.SimpleNamespace(refusal=None, content=_verdict_json(_n_files(content)))
                return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

        class Files:
            def create(self, file, purpose):
                outer.uploaded = file.read().decode("utf-8")
                return types.SimpleNamespace(id="file-in")

            def content(self, file_id):
                lines = []
                for raw in outer.uploaded.splitlines():
                    req = json.loads(raw)
                    content = req["body"]["messages"][1]["content"]
                    outer.sent.append(content)
                    lines.append(json.dumps({"custom_id": req["custom_id"], "response": {
                        "status_code": 200, "body": {"choices": [{"message": {
                            "content": _verdict_json(_n_files(content)), "refusal": None}}]}}}))
                return types.SimpleNamespace(text="\n".join(lines))

        class Batches:
            def create(self, **kw):
                outer.batches_made["b1"] = 0
                return types.SimpleNamespace(id="b1", status="validating")

            def retrieve(self, bid):
                outer.batches_made[bid] += 1      # first poll: still running, then done
                done = outer.batches_made[bid] > 1
                return types.SimpleNamespace(
                    id=bid, status="completed" if done else "in_progress",
                    output_file_id="file-out" if done else None, error_file_id=None,
                    request_counts=types.SimpleNamespace(completed=1, total=2))

        self.chat = types.SimpleNamespace(completions=Completions())
        self.files = Files()
        self.batches = Batches()


@pytest.fixture()
def fake_openai(monkeypatch):
    import openai
    made = []

    def factory(**kw):
        c = FakeOpenAI(**kw)
        made.append(c)
        return c
    monkeypatch.setattr(openai, "OpenAI", factory)
    return made


def _ai_cfg(cfg, tmp_path, monkeypatch, **over):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    key_file = tmp_path / "api-key.txt"
    key_file.write_text("# Paste your key below\nsk-test-from-file\n", encoding="utf-8")
    cfg.ai_key_file = key_file
    cfg.ai_batch = "never"
    for k, v in over.items():
        setattr(cfg, k, v)
    return cfg


def test_ai_reads_each_email_once_with_full_context(cfg, tmp_path, monkeypatch, fake_openai):
    from mailsorter.ai import ai_pass
    _ai_cfg(cfg, tmp_path, monkeypatch)
    make_demo(cfg, n_emails=150)
    classify_all(cfg)
    conn = db.connect(cfg.db_path)
    n_emails = conn.execute("""SELECT COUNT(DISTINCT entry_id) FROM (
        SELECT a.entry_id, ROW_NUMBER() OVER (PARTITION BY a.sha256 ORDER BY m.received, a.id) rn
        FROM attachments a JOIN messages m USING(entry_id)) WHERE rn = 1""").fetchone()[0]
    ai_pass(cfg, conn)
    client = fake_openai[0]
    assert client.kw["api_key"] == "sk-test-from-file"
    assert len(client.sent) == n_emails                       # one request per email, none repeated
    joined = "\n".join(client.sent)
    assert "ABCDE1234F" not in joined and "@sunrisepharma.com" in joined   # masked, domain kept
    assert "rahul.mehta@" not in joined
    assert "To: " in joined and "CC: " in joined and "FORWARDED MESSAGE" in joined
    assert "KYC document - text not sent" in joined
    got = conn.execute("SELECT DISTINCT category, method, client FROM files").fetchall()
    assert [tuple(r) for r in got] == [("Claims", "ai", "Sunrise Pharma")]
    assert conn.execute("SELECT COUNT(*) FROM messages WHERE summary != ''").fetchone()[0] == n_emails

    # A second run sends nothing (and costs nothing)
    before = sum(len(c.sent) for c in fake_openai)
    ai_pass(cfg, conn)
    assert sum(len(c.sent) for c in fake_openai) == before


def test_ai_scope_unsure_sends_only_unsure(cfg, tmp_path, monkeypatch, fake_openai):
    from mailsorter.ai import ai_pass
    _ai_cfg(cfg, tmp_path, monkeypatch, ai_scope="unsure")
    make_demo(cfg, n_emails=150)
    classify_all(cfg)
    conn = db.connect(cfg.db_path)
    ai_pass(cfg, conn)
    assert len(fake_openai[0].sent) < 10
    assert conn.execute("SELECT COUNT(*) FROM files WHERE method='rules'").fetchone()[0] > 50


def test_ai_batch_mode(cfg, tmp_path, monkeypatch, fake_openai):
    from mailsorter.ai import ai_pass
    _ai_cfg(cfg, tmp_path, monkeypatch, ai_batch="always")
    make_demo(cfg, n_emails=60)
    classify_all(cfg)
    conn = db.connect(cfg.db_path)
    ai_pass(cfg, conn, poll_seconds=0)
    client = fake_openai[0]
    assert client.uploaded.count("\n") >= 10                 # one JSONL line per email
    assert conn.execute("SELECT status FROM ai_batches").fetchone()[0] == "completed"
    assert conn.execute("SELECT COUNT(*) FROM messages WHERE ai_status='queued'").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM files WHERE method='ai'").fetchone()[0] == \
        conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]


def test_ai_budget_limit_stops_before_spending(cfg, tmp_path, monkeypatch, fake_openai, capsys):
    from mailsorter.ai import ai_pass
    _ai_cfg(cfg, tmp_path, monkeypatch, ai_max_cost_usd=0.0)
    make_demo(cfg, n_emails=40)
    classify_all(cfg)
    ai_pass(cfg, db.connect(cfg.db_path))
    assert "NOT started" in capsys.readouterr().out
    assert all(c.sent == [] for c in fake_openai)


def test_local_model_is_free_and_uses_ollama(cfg, tmp_path, monkeypatch, fake_openai, capsys):
    from mailsorter.ai import ai_pass
    _ai_cfg(cfg, tmp_path, monkeypatch, ai_provider="local", ai_model="qwen2.5:7b", ai_max_cost_usd=0.0)
    make_demo(cfg, n_emails=30)
    classify_all(cfg)
    ai_pass(cfg, db.connect(cfg.db_path))
    assert "free" in capsys.readouterr().out
    assert fake_openai[0].kw["base_url"] == "http://localhost:11434/v1"
    assert len(fake_openai[0].sent) > 0


def test_ai_with_anthropic(cfg, tmp_path, monkeypatch):
    import types
    import anthropic
    from mailsorter.ai import EmailVerdict, ai_pass
    sent = []

    class Messages:
        def parse(self, **kw):
            content = kw["messages"][0]["content"]
            sent.append(content)
            v = EmailVerdict.model_validate_json(_verdict_json(_n_files(content)))
            return types.SimpleNamespace(stop_reason="end_turn", parsed_output=v)
    monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: types.SimpleNamespace(messages=Messages()))
    _ai_cfg(cfg, tmp_path, monkeypatch, ai_provider="anthropic")
    make_demo(cfg, n_emails=30)
    classify_all(cfg)
    conn = db.connect(cfg.db_path)
    ai_pass(cfg, conn)
    assert sent and conn.execute("SELECT COUNT(*) FROM files WHERE method='ai'").fetchone()[0] > 0


def test_estimate_counts_tokens_and_cost(cfg):
    from mailsorter.ai import estimate
    make_demo(cfg, n_emails=100)
    classify_all(cfg)
    e = estimate(cfg, db.connect(cfg.db_path))
    assert e["emails"] > 0 and e["input_tokens"] > e["emails"] * 300
    assert e["cost_batch"] == pytest.approx(e["cost_live"] / 2)


def test_ai_skipped_without_key(cfg, monkeypatch, tmp_path, capsys):
    from mailsorter.ai import ai_pass
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg.ai_key_file = tmp_path / "missing.txt"
    make_demo(cfg, n_emails=20)
    classify_all(cfg)
    ai_pass(cfg, db.connect(cfg.db_path))
    assert "no API key" in capsys.readouterr().out
