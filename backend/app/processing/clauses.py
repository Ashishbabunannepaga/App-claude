"""Deterministic clause extraction: split policy wording into typed, citable clauses.

Rule-based on purpose — explainable, free to run, and a labelled base for training our own
classifier later. Every clause keeps its page and section so answers can cite it exactly.
"""

import re
from dataclasses import dataclass, field

from app.processing.chunking import _is_heading
from app.processing.text_utils import sentences

# Priority order: the first matching type is the clause's primary type; all matches become tags.
CLAUSE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("definition", re.compile(r"\bmeans\b|shall mean|is defined as|\brefers to\b", re.I)),
    (
        "exclusion",
        re.compile(
            r"not (covered|payable|admissible|included)|\bexcluded\b|\bexclusions?\b|will not be (paid|covered)"
            r"|\bno\b[^.]{0,40}\b(benefit|cover)\b[^.]{0,20}\b(is|are) payable",
            re.I,
        ),
    ),
    ("waiting_period", re.compile(r"waiting period|after \d+ (months|years|days) of", re.I)),
    (
        "limit",
        re.compile(
            r"\bup ?to\b|\bmaximum\b|sub-?limit|limited to|capped|\d+(\.\d+)?\s*% of|per (day|claim|delivery|"
            r"hospitali[sz]ation|year|policy year)|deductible|co-?pay",
            re.I,
        ),
    ),
    (
        "condition",
        re.compile(
            r"subject to|provided that|\bmust\b|within \d+ (days|hours)|prior (approval|intimation)|"
            r"pre-?authori[sz]ation|\binform\b|\bnotif",
            re.I,
        ),
    ),
    (
        "benefit",
        re.compile(r"\bcovered\b|\bpayable\b|\bbenefits?\b|reimburs|\bincluded\b|\bpaid\b|restoration|\bbonus\b", re.I),
    ),
]

CLAUSE_TYPES = [t for t, _ in CLAUSE_RULES]
_LABEL = re.compile(r"^([A-Z][A-Za-z0-9 /&()'\-]{2,45}):\s+(.+)$")


@dataclass
class Clause:
    clause_type: str
    title: str
    text: str
    page: int
    section: str | None
    order: int
    tags: list[str] = field(default_factory=list)


def classify(text: str) -> list[str]:
    return [name for name, rx in CLAUSE_RULES if rx.search(text)]


def _title(text: str) -> str:
    m = _LABEL.match(text)
    if m:
        return m.group(1).strip()
    words = re.sub(r"[^\w\s%-]", "", text).split()
    return " ".join(words[:6]) + ("…" if len(words) > 6 else "")


def extract_clauses(pages: list[str]) -> list[Clause]:
    clauses: list[Clause] = []
    section: str | None = None
    for page_no, page_text in enumerate(pages, start=1):
        for sentence in sentences(page_text):
            if _is_heading(sentence):
                section = sentence.rstrip(":")
                continue
            if len(sentence) < 25:
                continue
            tags = classify(sentence)
            if not tags:
                continue  # schedule values like "Policy No: …" carry no clause meaning
            clauses.append(Clause(tags[0], _title(sentence), sentence[:1000], page_no, section, len(clauses), tags))
    return clauses
