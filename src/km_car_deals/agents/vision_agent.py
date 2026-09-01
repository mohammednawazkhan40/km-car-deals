"""Vehicle Vision Agent.

Analyzes every photograph: classifies view, evaluates quality, detects obvious
duplicates, and conservatively reports visible damage. Never claims damage it
cannot confirm.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from km_car_deals.ai.provider import ai_provider
from km_car_deals.ai.vision import basic_image_info
from km_car_deals.models.vehicle import VehiclePhoto

logger = logging.getLogger(__name__)


class VehicleVisionAgent:
    def __init__(self, db: Session):
        self.db = db

    def analyze_photo(self, photo: VehiclePhoto) -> VehiclePhoto:
        """Run vision analysis on a single photo and persist results."""
        path = photo.file_path if Path(photo.file_path).is_absolute() else Path(photo.file_path)
        info = basic_image_info(str(path))
        photo.width = info.get("width")
        photo.height = info.get("height")
        photo.size_bytes = info.get("size_bytes")

        if ai_provider.name != "disabled":
            try:
                ai = ai_provider.analyze_photo(str(path))
                photo.category = ai.get("category", photo.category or "other")
                photo.quality_score = ai.get("quality_score")
                photo.blur_detected = ai.get("blur_detected")
                photo.lighting_ok = ai.get("lighting_ok")
                photo.composed_ok = ai.get("composed_ok")
                photo.damage_found = ai.get("damage_found") or []
                photo.analysis_notes = ai.get("notes")
            except Exception:
                logger.exception("AI vision failed; storing deterministic data")
                photo.category = photo.category or "other"
        else:
            photo.category = photo.category or "other"
            photo.analysis_notes = "AI vision disabled; deterministic analysis only."
        self.db.flush()
        return photo

    def detect_duplicates(self, photos: List[VehiclePhoto]) -> Dict[str, str]:
        """Return mapping of photo_id -> photo_id it is a duplicate of."""
        hashes: Dict[str, str] = {}
        dups: Dict[str, str] = {}
        for photo in photos:
            h = self._phash(photo)
            if not h:
                continue
            if h in hashes:
                dups[photo.photo_id] = hashes[h]
                photo.duplicate_of = hashes[h]
            else:
                hashes[h] = photo.photo_id
        self.db.flush()
        return dups

    def _phash(self, photo: VehiclePhoto) -> Optional[str]:
        """Perceptual hash (aHash) of the image for duplicate detection."""
        try:
            from PIL import Image

            path = photo.file_path
            with Image.open(path) as img:
                img = img.convert("L").resize((16, 16))
                pixels = list(img.getdata())
                avg = sum(pixels) / len(pixels)
                bits = "".join("1" if p >= avg else "0" for p in pixels)
                return format(int(bits, 2), "016x")[:16]
        except Exception:
            return None


def compute_sha256_photo(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()
