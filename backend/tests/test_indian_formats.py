"""Amounts and dates the way Indian policy schedules write them."""

from datetime import date
from decimal import Decimal

import pytest

from app.processing.extraction import validate_extraction
from app.processing.heuristics import amounts_in_text, find_premium, find_sum_insured, parse_amount, parse_date


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("5,00,000", 500000),
        ("Rs. 5,00,000/-", 500000),
        ("₹10 lakh", 1000000),
        ("10 Lakhs", 1000000),
        ("Rs.5 Lacs", 500000),
        ("5L", 500000),
        ("1.5 Cr", 15000000),
        ("1 crore", 10000000),
        ("1,00,00,000", 10000000),
        ("INR 25,000", 25000),
        ("₹ 18,450.00", 18450),
        ("2,50,000 (Two Lakh Fifty Thousand)", 250000),
        (500000, 500000),
    ],
)
def test_amounts(text, expected):
    assert parse_amount(text) == Decimal(expected)


@pytest.mark.parametrize("text", ["10% of sum insured", "Up to 1% of SI per day", "co-pay 20 %", "abc", "", 0, None])
def test_not_amounts(text):
    assert parse_amount(text) is None


@pytest.mark.parametrize(
    "text",
    ["01/04/2026", "1-Apr-2026", "01 April 2026", "2026-04-01", "April 1, 2026", "1st April 2026", "Apr 01 2026"],
)
def test_dates(text):
    assert parse_date(text) == date(2026, 4, 1)


def test_amounts_in_text_applies_units_and_skips_percentages():
    text = "Room rent: 1% of Sum Insured, max Rs. 5,000. Co-pay 10%. Sum Insured Rs 5 Lakh."
    assert amounts_in_text(text) == {5000, 500000}


def test_regex_fallback_reads_lakh_amounts():
    assert find_sum_insured("Sum Insured: Rs. 5 Lakh") == Decimal(500000)
    assert find_premium("Total Premium: Rs. 18,450/-") == Decimal(18450)


def test_correct_ai_amount_written_in_lakh_is_not_flagged():
    """Gemini returns 500000; the schedule says "Rs. 5 Lakh". That is a match, not a doubt."""
    text = "Sum Insured: Rs. 5 Lakh\nPremium: Rs. 18,450"
    raw = {
        "policy_type": "health",
        "fields": {
            "sum_insured": {"value": 500000, "confidence": 0.95},
            "premium": {"value": "18450", "confidence": 0.95},
        },
    }
    result = validate_extraction(raw, text)
    assert result.values["sum_insured"] == Decimal(500000)
    assert result.confidence["sum_insured"] == 0.95
    assert result.confidence["premium"] == 0.95


def test_ai_amount_with_unit_text_is_still_read():
    raw = {"policy_type": "health", "fields": {"sum_insured": {"value": "₹10 lakh", "confidence": 0.9}}}
    result = validate_extraction(raw, "Sum Insured 10 Lakhs")
    assert result.values["sum_insured"] == Decimal(1000000)
    assert result.confidence["sum_insured"] == 0.9
