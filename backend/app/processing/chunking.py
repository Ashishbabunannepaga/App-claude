import re
from dataclasses import dataclass

CHUNK_CHARS = 1000
OVERLAP_CHARS = 150

_HEADING = re.compile(r"^(?:\d+(?:\.\d+)*[.)]?\s+)?[A-Z][A-Za-z0-9 &/,\-()]{2,80}:?$")


@dataclass
class Chunk:
    index: int
    page: int
    section: str | None
    content: str


def _is_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 80 or line.endswith("."):
        return False
    return bool(_HEADING.match(line)) and (line.isupper() or line.istitle() or line[0].isdigit())


def chunk_pages(pages: list[str]) -> list[Chunk]:
    """Page-aware chunking; each chunk remembers the most recent heading seen as its section."""
    chunks: list[Chunk] = []
    section: str | None = None
    for page_no, text in enumerate(pages, start=1):
        buf = ""
        buf_section = section
        for line in text.splitlines():
            if _is_heading(line):
                section = line.strip().rstrip(":")
                if not buf.strip():
                    buf_section = section
            buf += line + "\n"
            if len(buf) >= CHUNK_CHARS:
                chunks.append(Chunk(len(chunks), page_no, buf_section, buf.strip()))
                buf = buf[-OVERLAP_CHARS:]
                buf_section = section
        if buf.strip() and (not chunks or chunks[-1].content != buf.strip()):
            chunks.append(Chunk(len(chunks), page_no, buf_section, buf.strip()))
    return [c for c in chunks if len(c.content) >= 20]
