import io
from dataclasses import dataclass
from functools import lru_cache

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.config import get_settings

MIN_CHARS_PER_PAGE = 50
OCR_DPI_SCALE = 200 / 72


class ExtractionError(Exception):
    """`code` is user-safe and returned by the API."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass
class ExtractedText:
    pages: list[str]
    method: str  # "text" or "ocr"

    @property
    def full_text(self) -> str:
        return "\n\n".join(f"[Page {i}]\n{p}" for i, p in enumerate(self.pages, start=1))


def _ocr_image(image) -> str:
    provider = get_settings().ocr_provider
    if provider == "none":
        raise ExtractionError("ocr_unavailable")
    if provider in ("gemini", "openai"):
        return _vision_ocr(image, provider)
    if provider == "paddle":
        return _paddle_ocr(image)
    import pytesseract

    try:
        langs = get_settings().ocr_languages
        available = set(pytesseract.get_languages(config=""))
        langs = "+".join(lang for lang in langs.split("+") if lang in available) or "eng"
        return pytesseract.image_to_string(image, lang=langs)
    except pytesseract.TesseractNotFoundError as exc:
        # Tesseract is a system program, often missing on Windows PCs and slim servers. With an AI key
        # (Gemini or OpenAI), photos and scanned PDFs are read by a vision model instead.
        fallback = _vision_fallback()
        if fallback is None:
            raise ExtractionError("ocr_unavailable") from exc
        return _vision_ocr(image, fallback)


def _vision_fallback() -> str | None:
    """Vision OCR for when Tesseract is missing: the main AI provider if it has a key, else any keyed one."""
    s = get_settings()
    keyed = [name for name, key in (("gemini", s.gemini_api_key), ("openai", s.openai_api_key)) if key]
    if s.ai_provider in keyed:
        return s.ai_provider
    return keyed[0] if keyed else None


VISION_OCR_MAX_SIDE = 2000  # px; enough for small print, keeps each request well under inline image limits


def _vision_ocr(image, provider: str) -> str:
    s = get_settings()
    key = s.gemini_api_key if provider == "gemini" else s.openai_api_key
    if not key:
        raise ExtractionError("ocr_unavailable")
    img = image.convert("RGB")
    img.thumbnail((VISION_OCR_MAX_SIDE, VISION_OCR_MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    if provider == "gemini":
        from app.ai.providers.gemini import GeminiProvider

        engine = GeminiProvider(key, s.gemini_model, s.ai_timeout_seconds)
    else:
        from app.ai.providers.openai import OpenAIProvider

        engine = OpenAIProvider(key, s.openai_model, s.ai_timeout_seconds)
    return engine.transcribe(buf.getvalue(), "image/jpeg")


@lru_cache
def _paddle_engine():
    try:
        from paddleocr import PaddleOCR  # installed only in the ML worker image (requirements-ml.txt)
    except ImportError as exc:
        raise ExtractionError("ocr_unavailable") from exc
    return PaddleOCR(use_angle_cls=True, lang=get_settings().ocr_paddle_lang, show_log=False)


def _paddle_ocr(image) -> str:
    """PaddleOCR: better than Tesseract on phone photos, skew and stamps. Lines are re-ordered
    top-to-bottom, left-to-right so clause and field extraction see natural reading order."""
    import numpy as np

    result = _paddle_engine().ocr(np.array(image.convert("RGB")), cls=True) or []
    lines = [
        (box[0][1], box[0][0], text) for page in result for box, (text, confidence) in (page or []) if confidence >= 0.5
    ]
    rows: list[list[tuple[float, float, str]]] = []
    for y, x, text in sorted(lines):
        if rows and abs(rows[-1][0][0] - y) < 12:  # same visual line
            rows[-1].append((y, x, text))
        else:
            rows.append([(y, x, text)])
    return "\n".join(" ".join(t for _, _, t in sorted(row, key=lambda r: r[1])) for row in rows)


def _ocr_pdf(data: bytes) -> list[str]:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(data)
    try:
        return [_ocr_image(page.render(scale=OCR_DPI_SCALE).to_pil()) for page in pdf]
    finally:
        pdf.close()


def _open_without_password(reader: PdfReader) -> bool:
    try:
        return bool(reader.decrypt(""))
    except Exception:  # noqa: BLE001 - unsupported encryption counts as locked
        return False


def extract_text(data: bytes, content_type: str) -> ExtractedText:
    if content_type == "application/pdf":
        try:
            reader = PdfReader(io.BytesIO(data))
            # Many insurers lock their PDFs only against editing or printing: those open with an
            # empty password. Only a PDF that needs a real password to open is refused.
            if reader.is_encrypted and not _open_without_password(reader):
                raise ExtractionError("pdf_password_protected")
            if len(reader.pages) > get_settings().max_pdf_pages:
                raise ExtractionError("pdf_too_many_pages")
            pages = [(page.extract_text() or "").strip() for page in reader.pages]
        except PdfReadError as exc:
            raise ExtractionError("pdf_unreadable") from exc
        if pages and sum(len(p) for p in pages) / len(pages) >= MIN_CHARS_PER_PAGE:
            return ExtractedText(pages, "text")
        pages = [p.strip() for p in _ocr_pdf(data)]  # scanned PDF
        method = "ocr"
    else:
        from PIL import Image

        with Image.open(io.BytesIO(data)) as img:
            pages = [_ocr_image(img.convert("RGB")).strip()]
        method = "ocr"
    if sum(len(p) for p in pages) < MIN_CHARS_PER_PAGE:
        raise ExtractionError("no_text_found")
    return ExtractedText(pages, method)
