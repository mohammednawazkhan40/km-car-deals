"""Local OCR helpers using pytesseract (offline fallback)."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ocr_file_local(file_path: str) -> str:
    """Run Tesseract OCR on an image. Empty string if unavailable/PDF."""
    path = Path(file_path)
    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            return _ocr_pdf(path)
        import pytesseract  # type: ignore
        from PIL import Image

        img = Image.open(path)
        return pytesseract.image_to_string(img)
    except Exception:
        logger.exception("Local OCR failed for %s", file_path)
        return ""


def _ocr_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        parts.append(txt)
    return "\n".join(parts)
