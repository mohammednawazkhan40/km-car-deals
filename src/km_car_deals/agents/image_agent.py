"""Vehicle Image Agent.

For each original photo, keep the original unchanged and generate:
processed/web/social/thumbnail variants. Also merges them into the vehicle's
photo set while preserving provenance.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from km_car_deals.core.config import settings
from km_car_deals.image_processing.processor import generate_variants
from km_car_deals.models.enums import PhotoVariant
from km_car_deals.models.vehicle import VehiclePhoto
from km_car_deals.utils import paths

logger = logging.getLogger(__name__)


class VehicleImageAgent:
    def __init__(self, db: Session):
        self.db = db

    def process_vehicle_photos(
        self,
        vehicle_id: str,
        photos: List[VehiclePhoto],
        background: Optional[str] = None,
    ) -> List[VehiclePhoto]:
        """Generate variants for all original photos of a vehicle."""
        root = paths.upload_root() / vehicle_id
        new_photos: List[VehiclePhoto] = []
        for photo in photos:
            if photo.variant != PhotoVariant.ORIGINAL.value:
                continue
            orig_path = photo.file_path
            if not Path(orig_path).is_absolute():
                orig_path = str(paths.upload_root().resolve() / orig_path)
            if not Path(orig_path).exists():
                logger.warning("Original photo missing: %s", orig_path)
                continue
            variants = generate_variants(
                orig_path, str(root), background=background or settings.DEFAULT_BACKGROUND
            )
            for variant, out_path in variants.items():
                if variant == PhotoVariant.ORIGINAL.value:
                    continue
                new_photos.append(
                    VehiclePhoto(
                        vehicle_id=vehicle_id,
                        variant=variant,
                        category=photo.category,
                        file_path=str(out_path),
                        original_file_name=photo.original_file_name,
                        is_primary=photo.is_primary if variant == PhotoVariant.WEB.value else False,
                    )
                )
        for p in new_photos:
            self.db.add(p)
        self.db.flush()
        return new_photos
