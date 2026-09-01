"""Storage path helpers for uploaded files."""

from __future__ import annotations

import uuid
from pathlib import Path

from km_car_deals.core.config import settings


def _resolve(data_root: str) -> Path:
    root = Path(data_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def upload_root() -> Path:
    return _resolve(settings.UPLOAD_DIR)


def export_root() -> Path:
    return _resolve(settings.EXPORT_DIR)


def _safe_stem(name: str) -> str:
    return Path(name).stem[:40].replace(" ", "_")


def store_upload(data: bytes, original_name: str, subdir: str = "raw") -> Path:
    """Store an upload on disk and return its absolute path."""
    base = upload_root() / subdir
    base.mkdir(parents=True, exist_ok=True)
    ext = Path(original_name).suffix.lower()
    filename = f"{uuid.uuid4().hex[:10]}_{_safe_stem(original_name)}{ext}"
    path = base / filename
    path.write_bytes(data)
    return path


def relative_to_upload_root(path: Path) -> str:
    """Return a path string that survives moving the repo (relative to cwd)."""
    try:
        return str(path.relative_to(upload_root().resolve()))
    except ValueError:
        return str(path)
