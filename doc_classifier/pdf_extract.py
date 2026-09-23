"""PDF text extraction. No CLI dependencies."""
from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PDFExtractionError(Exception):
    """Raised when text cannot be extracted from a PDF."""


def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract raw text from a PDF file.

    Raises:
        PDFExtractionError: if the file can't be read or contains no extractable
            text (e.g. a scanned/image-only PDF).
    """
    path = Path(file_path)
    if not path.exists():
        raise PDFExtractionError(f"File not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise PDFExtractionError(f"Not a PDF file: {path}")

    try:
        reader = PdfReader(str(path))
    except (PdfReadError, OSError) as exc:
        raise PDFExtractionError(f"Could not read PDF ({exc}). File may be corrupt.") from exc

    pages_text = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001 - a single bad page shouldn't abort extraction
            continue

    text = "\n".join(pages_text).strip()
    if not text:
        raise PDFExtractionError(
            "No extractable text found in PDF; it may be a scanned/image-only PDF."
        )
    return text
