from datetime import date
from decimal import Decimal

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


MOTOR_TEXT = (
    "Policy No. 6203516874 02 00\nPeriod 04/10/2026 to 03/10/2027\nTotal Policy Premium 13152\nTotal IDV 426164\n"
    "The preceding year 20%, preceding two consecutive years 25%\n"
    "5.Claim in Previous Policy Period: Yes\n6.NCB in Previous Policy: 25 %\n7.NCB Claimed: NA\n"
)


def _motor(ncb):
    return {"policy_type": "motor", "fields": {}, "details": {"ncb_percentage": ncb, "registration_number": "TS 08"}}


def test_previous_policy_ncb_is_not_this_policys_ncb():
    r = validate_extraction(_motor("25"), MOTOR_TEXT)
    assert "ncb_percentage" not in r.details
    assert r.details["registration_number"] == "TS08"


def test_a_claimed_ncb_is_kept():
    text = MOTOR_TEXT.replace("NCB Claimed: NA", "NCB Claimed: 25%")
    assert validate_extraction(_motor("25"), text).details["ncb_percentage"] == "25"
    for written in ("NCB claimed : Nil", "NCB Claimed:0%", "NCB claimed - N/A"):
        text = MOTOR_TEXT.replace("NCB Claimed: NA", written)
        assert "ncb_percentage" not in validate_extraction(_motor("25"), text).details, written


def test_a_discount_line_beats_a_proposal_ncb_claimed_na():
    # Tata AIG: the proposal section says "NCB Claimed: NA" but the premium schedule applies the discount.
    for line in ("Less : No claim bonus (25%) 527.76", "No claim bonus 25% -760.84", "NCB Discount(25%) 165.57"):
        assert validate_extraction(_motor("25"), MOTOR_TEXT + line).details["ncb_percentage"] == "25", line
    # A different percentage, or the previous policy's NCB, does not count.
    assert "ncb_percentage" not in validate_extraction(_motor("25"), MOTOR_TEXT + "No claim bonus (50%)").details


def test_registration_number_is_normalised():
    for written in ("AP 39 KS 7117", "AP-39-KS-7117", "ap39ks7117"):
        raw = {"policy_type": "motor", "fields": {}, "details": {"registration_number": written}}
        assert validate_extraction(raw, MOTOR_TEXT).details["registration_number"] == "AP39KS7117"


def _premium(value, text):
    raw = {"policy_type": "motor", "fields": {"premium": {"value": value, "confidence": 0.9}}}
    return validate_extraction(raw, text).values["premium"]


def test_net_premium_is_replaced_by_the_total_with_gst():
    # Table text loses the labels, so the check is arithmetic: net + 18% GST, with the GST figure shown.
    digit = "Net Premium Final Premium\n8758.91\nIGST @18% (1576.61)\n10335.52\n"
    assert _premium("8758.91", digit) == Decimal("10335.52")
    assert _premium("10335.52", digit) == Decimal("10335.52")
    # GST split into CGST + SGST, rounded by the insurer.
    split = "Net Premium 13,752.00 CGST 1,237.68 SGST 1,237.68 Final Premium 16,227.00"
    assert _premium("13752", split) == Decimal("16227.00")
    # No GST line (health with no tax): left alone.
    health = "Basic Premium 11,498.34 Stamp Duty 1.00 Total Premium 11,499.00"
    assert _premium("11498.34", health) == Decimal("11498.34")
