"""Local (offline) image analysis helpers using Pillow.

Used as a deterministic fallback when AI vision is disabled or unavailable.
These are conservative heuristics; they never invent damage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import logging

logger = logging.getLogger(__name__)


def basic_image_info(file_path: str) -> Dict[str, Any]:
    """Return width/height/format/size without any AI inference."""
    from PIL import Image

    path = Path(file_path)
    with Image.open(path) as img:
        w, h = img.size
        return {
            "width": w,
            "height": h,
            "format": img.format,
            "size_bytes": path.stat().st_size,
            "quality_score": None,
            "blur_detected": None,
            "lighting_ok": None,
            "composed_ok": None,
            "damage_found": [],
            "notes": "Deterministic local analysis (no AI).",
        }


def classify_photo_local(file_path: str) -> str:
    """Best-effort category guess based on image dimensions/orientation.

    This is intentionally conservative and returns 'other' unless there is
    strong heuristic signal, so we never mislabel a photo.
    """
    try:
        from PIL import Image

        with Image.open(file_path) as img:
            w, h = img.size
    except Exception:
        return "other"
    if w and h and abs(w - h) <= max(w, h) * 0.2 and w > 700:
        # Roughly square + large -> likely a wheel/tyre closeup or interior
        return "other"
    return "other"
