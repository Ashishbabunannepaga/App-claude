"""Indian-language → English insurance glossary.

Policy wordings are almost always English. When a question is asked in Hindi (or Hinglish), these
terms are added to the search query so keyword retrieval still finds the right clauses. Multilingual
embeddings (bge-m3) handle the rest. Extend per language as real user questions come in.
"""

import re

GLOSSARY: dict[str, str] = {
    # Hindi (Devanagari)
    "मातृत्व": "maternity",
    "प्रसूति": "maternity",
    "डिलीवरी": "delivery",
    "गर्भावस्था": "pregnancy maternity",
    "कमरा": "room",
    "कमरे": "room",
    "किराया": "rent",
    "किराए": "rent",
    "दांत": "dental",
    "दाँत": "dental",
    "आंख": "eye",
    "एम्बुलेंस": "ambulance",
    "प्रतीक्षा": "waiting",
    "इंतजार": "waiting",
    "अवधि": "period",
    "पहले": "pre-existing",
    "बीमारी": "disease illness",
    "बीमारियां": "diseases",
    "बाहर": "excluded",
    "शामिल": "covered included",
    "कवर": "covered",
    "कवरेज": "coverage",
    "नॉमिनी": "nominee",
    "नामांकित": "nominee",
    "दावा": "claim",
    "क्लेम": "claim",
    "प्रीमियम": "premium",
    "बीमा": "insurance",
    "अस्पताल": "hospital hospitalisation",
    "भर्ती": "admission hospitalisation",
    "इलाज": "treatment",
    "ऑपरेशन": "surgery",
    "सर्जरी": "surgery",
    "को-पेमेंट": "co-payment",
    "कटौती": "deductible",
    "बोनस": "bonus",
    "नवीनीकरण": "renewal",
    "मृत्यु": "death",
    "परिपक्वता": "maturity",
    "गाड़ी": "vehicle",
    "इंजन": "engine",
    "दुर्घटना": "accident",
    "माता": "parents",
    "पिता": "parents",
    "बच्चे": "child",
    # Hinglish (Latin script)
    "kamra": "room",
    "kiraya": "rent",
    "daant": "dental",
    "bimari": "disease",
    "ilaj": "treatment",
    "dawa": "claim",
    "bima": "insurance",
    "aspatal": "hospital",
    "gaadi": "vehicle",
}

# Split on spaces/punctuation only: Devanagari vowel signs are not regex "word" characters.
_WORD = re.compile(r"[^\s?.,!;:'\"()।॥]+")


# Insurers sell the same cover under different names. A question in one name must find the wording in another:
# TATA AIG calls zero depreciation "Depreciation Reimbursement", others "Nil Depreciation" or "Bumper to Bumper".
COVER_SYNONYMS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b(zero|nil|0)[\s-]*dep(reciation)?\b"
            r"|bumper[\s-]*to[\s-]*bumper"
            r"|depreciation (reimbursement|waiver|cover)"
        ),
        "depreciation reimbursement nil depreciation zero depreciation bumper to bumper",
    ),
    (
        re.compile(r"\bengine (protect(ion|or)?|secure|guard|cover)\b|hydrostatic"),
        "engine secure engine protection engine protector hydrostatic",
    ),
    (re.compile(r"\b(rsa|road\s*side assistance|roadside)\b"), "road side assistance roadside assistance"),
    (
        re.compile(r"\b(rti|return to invoice|invoice cover|invoice protect)"),
        "return to invoice invoice price",
    ),
    (re.compile(r"\bconsumables?\b"), "consumable expenses consumables"),
    (re.compile(r"\b(ncb|no claim bonus) protect"), "ncb protection no claim bonus protection"),
    (re.compile(r"\bkey (replacement|loss|protect)"), "key replacement"),
    (re.compile(r"\b(ped|pre[\s-]?existing)"), "pre-existing disease waiting period"),
    (re.compile(r"\b(opd|out[\s-]?patient)\b"), "out-patient opd"),
    (re.compile(r"\bco[\s-]?pay"), "co-payment co-pay"),
]


def english_terms(question: str) -> str:
    """English keywords for any glossary words or cover names in the question ('' if none)."""
    lowered = question.lower()
    found = [GLOSSARY[w] for w in _WORD.findall(lowered) if w in GLOSSARY]
    found += [terms for pattern, terms in COVER_SYNONYMS if pattern.search(lowered)]
    return " ".join(dict.fromkeys(found))
