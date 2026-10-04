"""Deterministic, regex-based helpers.

Used (a) to cross-validate AI extraction and (b) by the MOCK AI provider for offline development.
They are intentionally conservative: returning None is better than a wrong value.
"""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

KNOWN_INSURERS = [
    "ICICI Lombard",
    "HDFC ERGO",
    "Star Health",
    "Niva Bupa",
    "Care Health",
    "Bajaj Allianz",
    "Tata AIG",
    "Aditya Birla",
    "ManipalCigna",
    "SBI General",
    "New India Assurance",
    "United India",
    "Oriental Insurance",
    "National Insurance",
    "Reliance General",
    "Digit",
    "Acko",
    "Go Digit",
    "Royal Sundaram",
    "Cholamandalam",
    "Kotak General",
    "Future Generali",
    "IFFCO Tokio",
    "Liberty General",
    "Magma HDI",
    "Zuno",
    "LIC",
    "HDFC Life",
    "ICICI Prudential",
    "SBI Life",
    "Max Life",
    "Axis Max Life",
    "Tata AIA",
    "Bajaj Allianz Life",
    "Kotak Life",
    "PNB MetLife",
    "Aditya Birla Sun Life",
    "Canara HSBC",
    "Edelweiss Tokio",
    "Bharti AXA",
]

TYPE_KEYWORDS = {
    "health": [
        "health insurance",
        "hospitali",
        "mediclaim",
        "sum insured",
        "room rent",
        "cashless",
        "pre-existing",
        "tpa",
        "day care",
    ],
    "life": [
        "life insurance",
        "sum assured",
        "death benefit",
        "maturity",
        "nominee",
        "term plan",
        "ulip",
        "surrender value",
        "life assured",
    ],
    "motor": [
        "motor",
        "vehicle",
        "idv",
        "registration no",
        "chassis",
        "engine no",
        "own damage",
        "third party",
        "zero depreciation",
        "two wheeler",
        "private car",
    ],
}

_POLICY_NO = re.compile(r"policy\s*(?:no\.?|number|#)\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-]{5,40})", re.IGNORECASE)
_DATE = (
    r"(\d{1,2}[\-/\.]\d{1,2}[\-/\.]\d{2,4}|\d{1,2}[\s\-](?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
    r"[a-z]*[\s\-,]+\d{4}|\d{4}-\d{2}-\d{2})"
)
_START = re.compile(r"(?:start|from|commencement|inception|effective)[^\n\d]{0,40}" + _DATE, re.IGNORECASE)
_END = re.compile(r"(?:end|to|expiry|expiring|till|valid up ?to|until)[^\n\d]{0,40}" + _DATE, re.IGNORECASE)
_AMOUNT = r"(?:rs\.?|inr|₹)?\s*([0-9][0-9,]*(?:\.\d{1,2})?)"
_PREMIUM = re.compile(r"(?:total\s+)?premium[^\n\d₹]{0,40}" + _AMOUNT, re.IGNORECASE)
_SUM_INSURED = re.compile(
    r"(?:sum\s+insured|sum\s+assured|cover(?:age)?\s+amount|idv)[^\n\d₹]{0,40}" + _AMOUNT, re.IGNORECASE
)

_DATE_FORMATS = [
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%d/%m/%y",
    "%d-%m-%y",
    "%Y-%m-%d",
    "%d %b %Y",
    "%d %B %Y",
    "%d-%b-%Y",
    "%d %b, %Y",
    "%d %B, %Y",
]


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    v = re.sub(r"\s+", " ", value.strip().replace("Sept", "Sep").replace("sept", "sep"))
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(value: str | float | int | None) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        amount = Decimal(str(value).replace(",", "").replace("₹", "").strip())
    except InvalidOperation:
        return None
    return amount if amount > 0 else None


def normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def classify(text: str) -> str:
    lower = text.lower()
    scores = {t: sum(lower.count(k) for k in kws) for t, kws in TYPE_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


def find_insurer(text: str) -> str | None:
    lower = text.lower()
    hits = [(lower.find(name.lower()), name) for name in KNOWN_INSURERS if name.lower() in lower]
    return min(hits)[1] if hits else None


def find_policy_number(text: str) -> str | None:
    m = _POLICY_NO.search(text)
    return m.group(1).strip().rstrip(".") if m else None


def find_dates(text: str) -> tuple[date | None, date | None]:
    s = _START.search(text)
    e = _END.search(text, s.end() if s else 0) or _END.search(text)
    return (parse_date(s.group(1)) if s else None, parse_date(e.group(1)) if e else None)


def find_premium(text: str) -> Decimal | None:
    m = _PREMIUM.search(text)
    return parse_amount(m.group(1)) if m else None


def find_sum_insured(text: str) -> Decimal | None:
    m = _SUM_INSURED.search(text)
    return parse_amount(m.group(1)) if m else None
