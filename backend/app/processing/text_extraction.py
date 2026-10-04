import io
from dataclasses import dataclass

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
    if get_settings().ocr_provider == "none":
        raise ExtractionError("ocr_unavailable")
    import pytesseract

    try:
        return pytesseract.image_to_string(image, lang="eng")
    except pytesseract.TesseractNotFoundError as exc:
        raise ExtractionError("ocr_unavailable") from exc


def _ocr_pdf(data: bytes) -> list[str]:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(data)
    try:
        return [_ocr_image(page.render(scale=OCR_DPI_SCALE).to_pil()) for page in pdf]
    finally:
        pdf.close()


def extract_text(data: bytes, content_type: str) -> ExtractedText:
    if content_type == "application/pdf":
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
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
