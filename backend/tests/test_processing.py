from datetime import date

from app.processing import heuristics as h
from app.processing.chunking import chunk_pages
from app.processing.extraction import validate_extraction

TEXT = "Policy Number: ABC123456\nPeriod From 01/04/2026 To 31/03/2027\nPremium Rs. 12,000\nSum Insured 5,00,000"


def raw(**fields):
    return {"policy_type": "health", "fields": {k: {"value": v, "confidence": 0.95} for k, v in fields.items()}}


def test_validation_accepts_grounded_values():
    r = validate_extraction(
        raw(
            policy_number="ABC123456",
            start_date="2026-04-01",
            end_date="2027-03-31",
            premium=12000,
            sum_insured="500000",
        ),
        TEXT,
    )
    assert r.values["start_date"] == date(2026, 4, 1)
    assert r.confidence["policy_number"] == 0.95
    assert r.confidence["premium"] == 0.95


def test_validation_penalises_hallucinated_values():
    r = validate_extraction(
        raw(
            policy_number="ZZZ999999",
            premium=99999,
            start_date="2027-04-01",
            end_date="2026-03-31",
            payment_frequency="weekly",
        ),
        TEXT,
    )
    assert r.confidence["policy_number"] <= 0.3
    assert r.confidence["premium"] <= 0.4
    assert r.confidence["start_date"] <= 0.2
    assert r.values["payment_frequency"] is None


def test_invalid_type_falls_back_to_classifier_and_filters_details():
    r = validate_extraction(
        {"policy_type": "spaceship", "fields": {}, "details": {"idv": "1", "maternity": "yes"}}, TEXT
    )
    assert r.policy_type == "health"
    assert r.details == {"maternity": "yes"}


def test_heuristics():
    assert h.parse_date("5 Sept 2026") == date(2026, 9, 5)
    assert h.parse_amount("₹ 1,00,000") == 100000
    assert h.classify("Vehicle IDV and own damage cover") == "motor"
    assert h.find_policy_number(TEXT) == "ABC123456"


def test_chunking_tracks_pages_and_sections():
    pages = ["INTRODUCTION\n" + "word " * 300, "EXCLUSIONS\nCosmetic surgery is not covered under this policy."]
    chunks = chunk_pages(pages)
    assert chunks[0].page == 1 and chunks[0].section == "INTRODUCTION"
    assert chunks[-1].page == 2 and chunks[-1].section == "EXCLUSIONS"
