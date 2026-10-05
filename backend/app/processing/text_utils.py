"""Text helpers shared by clause extraction and the offline mock provider."""

import re

_SPLIT = re.compile(r"(?<=[.!?])(?<!Rs\.)(?<!No\.)\s+(?=[A-Z(])")


def sentences(text: str) -> list[str]:
    """Rebuild sentences from PDF lines: a line continues the previous one when that line has no
    closing punctuation and this one starts in lower case; headings stay on their own."""
    paragraphs: list[str] = []
    for line in (ln.strip() for ln in text.splitlines()):
        if not line or line.startswith("[Page"):
            continue
        if paragraphs and not paragraphs[-1].endswith((".", ":", "!", "?")) and line[0].islower():
            paragraphs[-1] += " " + line
        else:
            paragraphs.append(line)
    return [s.strip() for p in paragraphs for s in _SPLIT.split(p) if s.strip()]
