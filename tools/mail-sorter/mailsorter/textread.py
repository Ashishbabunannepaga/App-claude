"""Reads the first part of the text inside a document (PDF, Word, Excel, text).

Scanned PDFs (pictures of paper) have no text; those are sorted on file name,
subject and email body alone.
"""
from __future__ import annotations

import logging
from pathlib import Path

MAX_CHARS = 4000
logging.getLogger("pypdf").setLevel(logging.ERROR)


def _pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            return ""
    parts = []
    for page in reader.pages[:3]:
        parts.append(page.extract_text() or "")
        if sum(map(len, parts)) > MAX_CHARS:
            break
    return "\n".join(parts)


def _docx(path: Path) -> str:
    import docx
    d = docx.Document(str(path))
    parts = [p.text for p in d.paragraphs[:200]]
    for table in d.tables[:3]:
        for row in table.rows[:20]:
            parts.append(" | ".join(c.text for c in row.cells))
    return "\n".join(parts)


def _xlsx(path: Path) -> str:
    import openpyxl
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    parts = []
    try:
        for ws in wb.worksheets[:3]:
            parts.append(f"[sheet {ws.title}]")
            for row in ws.iter_rows(max_row=40, max_col=15, values_only=True):
                vals = [str(v) for v in row if v is not None]
                if vals:
                    parts.append(" | ".join(vals))
    finally:
        wb.close()
    return "\n".join(parts)


def _plain(path: Path) -> str:
    with open(path, "rb") as fh:
        raw = fh.read(MAX_CHARS * 2)
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


READERS = {
    ".pdf": _pdf,
    ".docx": _docx,
    ".xlsx": _xlsx, ".xlsm": _xlsx,
    ".txt": _plain, ".csv": _plain, ".htm": _plain, ".html": _plain,
}


def read_text(path: Path, ext: str) -> str:
    reader = READERS.get(ext)
    if reader is None or not path.exists():
        return ""
    try:
        text = reader(path) or ""
    except Exception:
        return ""
    return " ".join(text.split())[:MAX_CHARS]
