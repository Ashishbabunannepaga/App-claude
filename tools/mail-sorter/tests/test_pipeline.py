"""Run with:  python -m pytest tests  (from tools/mail-sorter)."""
from __future__ import annotations

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
    masked = mask("PAN ABCDE1234F aadhaar 1234 5678 9012 call 9876543210 a.b@x.com")
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


def test_ai_pass_with_fake_client(cfg, monkeypatch):
    """The AI step updates only unsure files, never KYC/high ones, and masks data."""
    import types
    import anthropic
    from mailsorter.ai import Verdict, ai_pass

    sent = []

    class FakeMessages:
        def parse(self, **kw):
            sent.append(kw["messages"][0]["content"])
            v = Verdict(category="claims", client="Sunrise Pharma", insurer="Tata AIG",
                        policy_no="P-1", reason="Hospital bill")
            return types.SimpleNamespace(stop_reason="end_turn", parsed_output=v)

    monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: types.SimpleNamespace(messages=FakeMessages()))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")

    make_demo(cfg, n_emails=150)
    classify_all(cfg)
    conn = db.connect(cfg.db_path)
    unsure = conn.execute("SELECT COUNT(*) FROM files WHERE confidence!='high' AND category!='KYC'").fetchone()[0]
    assert unsure >= 1
    ai_pass(cfg, conn)
    assert len(sent) == unsure
    assert all("ABCDE1234F" not in s for s in sent)
    got = conn.execute("SELECT category, method, client FROM files WHERE method='ai'").fetchall()
    assert got and all(tuple(r) == ("Claims", "ai", "Sunrise Pharma") for r in got)
