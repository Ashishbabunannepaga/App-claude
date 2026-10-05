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


def english_terms(question: str) -> str:
    """English keywords for any glossary words in the question ('' if none)."""
    found = [GLOSSARY[w] for w in _WORD.findall(question.lower()) if w in GLOSSARY]
    return " ".join(dict.fromkeys(found))
