"""The accuracy test tool: compares the reading pipeline's output with answers a person wrote down."""

import csv

import pytest

from app.scripts.eval_extraction import main, matches
from tests.conftest import make_pdf


@pytest.mark.parametrize(
    ("name", "expected", "got", "ok"),
    [
        ("insurer", "TATA AIG", "Tata AIG General Insurance", True),
        ("insurer", "HDFC ERGO", "TATA AIG", False),
        ("policy_number", "6203516874 02 00", "6203516874-02-00", True),
        ("start_date", "04/10/2026", "2026-10-04", True),
        ("start_date", "04/10/2026", "2026-04-10", False),  # day first, as Indian documents write it
        ("premium", "13,152", "13152.00", True),
        ("sum_insured", "5 lakh", "500000", True),
        ("premium", "13152", "13252", False),
        ("ncb_percentage", "-", None, True),  # "-" means it must be empty
        ("ncb_percentage", "-", "25", False),
        ("registration_number", "TS 08 HV 9458", "TS08 HV 9458", False),
        ("registration_number", "TS 08 HV 9458", "ts 08 hv 9458", True),
        ("payment_frequency", "annual", "annual", True),
    ],
)
def test_matching_rules(name, expected, got, ok):
    assert matches(name, expected, got) is ok


def test_end_to_end_report(tmp_path, capsys):
    (tmp_path / "star.pdf").write_bytes(make_pdf())
    assert main([str(tmp_path), "--template"]) == 0
    rows = list(csv.reader((tmp_path / "answers.csv").open()))
    assert rows[0][:3] == ["file", "policy_type", "insurer"] and rows[1][0] == "star.pdf"

    with (tmp_path / "answers.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "policy_type", "insurer", "policy_number", "start_date", "sum_insured", "premium"])
        w.writerow(["star.pdf", "health", "Star Health", "P/171100/01/2026/004521", "01/10/2026", "10 lakh", "99999"])
        w.writerow(["missing.pdf", "health", "", "", "", "", ""])

    assert main([str(tmp_path), "--min-accuracy", "0.9"]) == 1  # premium is deliberately wrong: 5/6
    out = capsys.readouterr().out
    assert "star.pdf: 5/6 fields right" in out
    assert "premium: expected '99999'" in out
    assert "missing.pdf: FAILED TO READ" in out
    assert list(tmp_path.glob("results-*.csv"))
    assert main([str(tmp_path), "--only", "motor"]) == 0  # no motor rows: nothing to check
