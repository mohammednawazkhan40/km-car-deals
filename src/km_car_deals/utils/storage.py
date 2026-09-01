"""File storage utilities (uploads, exports)."""

from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path
from typing import Optional

from km_car_deals.core.config import settings

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_DOC_EXT = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_EXCEL_EXT = {".xlsx", ".xlsm", ".xls"}


def safe_filename(original: str) -> str:
    """Produce a collision-safe, sanitized filename."""
    name = Path(original).name
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    return f"{uuid.uuid4().hex[:8]}_{stem[:40]}{suffix}"


def ensure_dir(path: str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def upload_dir() -> Path:
    return ensure_dir(settings.UPLOAD_DIR)


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def classify_mime(filename: str, mime: Optional[str] = None) -> str:
    ext = Path(filename).suffix.lower()
    if ext in ALLOWED_IMAGE_EXT:
        return "image"
    if ext == ".pdf":
        return "pdf"
    if ext in ALLOWED_EXCEL_EXT:
        return "excel"
    if mime and mime.startswith("image"):
        return "image"
    return "unknown"


def save_upload_bytes(data: bytes, original: str, subdir: str = "") -> str:
    """Persist raw upload bytes to disk; return relative path from upload dir."""
    base = upload_dir()
    if subdir:
        base = base / subdir
    base.mkdir(parents=True, exist_ok=True)
    name = safe_filename(original)
    path = base / name
    path.write_bytes(data)
    return str(path.relative_to(Path(settings.UPLOAD_DIR).resolve().parent)) if False else str(path)
