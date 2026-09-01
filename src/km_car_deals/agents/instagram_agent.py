"""Instagram Marketing Agent.

Generates captions, descriptions, hashtags, CTAs, photo selection and carousel
order for each vehicle. Always creates DRAFTS; publishing requires approval and
uses official Meta Graph API. Never scrapes Instagram.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from km_car_deals.ai.provider import ai_provider
from km_car_deals.core.config import settings
from km_car_deals.core.logging import get_logger
from km_car_deals.models.catalog import SocialContent
from km_car_deals.models.enums import (
    PublicationStatus,
    SocialContentStatus,
    VehicleStatus,
)
from km_car_deals.models.vehicle import Vehicle

logger = get_logger(__name__)

DEFAULT_HASHTAGS = ["#KMCarDeals", "#PreOwnedCars", "#UsedCars"]
DEFAULT_CTA = "DM KM Car Deals for price and availability."


class InstagramMarketingAgent:
    def __init__(self, db: Session):
        self.db = db

    def vehicle_info_payload(self, vehicle: Vehicle) -> dict:
        return {
            "name": vehicle.vehicle_name or f"{vehicle.manufacturer} {vehicle.model}",
            "year": vehicle.manufacturing_year,
            "fuel": vehicle.fuel_type,
            "transmission": vehicle.transmission,
            "mileage_km": vehicle.mileage_km,
            "color": vehicle.vehicle_color,
            "owner_count": vehicle.owner_count,
            "price": vehicle.selling_price,
            "location": vehicle.location,
        }

    def generate_draft(
        self,
        vehicle: Vehicle,
        caption_override: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
    ) -> SocialContent:
        """Build a draft social post. Publishing must go through approval."""
        payload = self.vehicle_info_payload(vehicle)
        caption, short_desc, tags, cta, photo_order = self._generate_with_ai(vehicle, caption_override, hashtags)

        if not photo_order:
            photo_order = self._format_photo_order(vehicle)

        content = SocialContent(
            vehicle_id=vehicle.vehicle_id,
            platform="INSTAGRAM",
            status=SocialContentStatus.DRAFT.value,
            caption=caption,
            short_description=short_desc,
            hashtags=tags,
            cta=cta,
            photo_order=photo_order,
        )
        self.db.add(content)
        self.db.flush()
        return content

    def _generate_with_ai(
        self,
        vehicle: Vehicle,
        caption_override: Optional[str],
        hashtags: Optional[List[str]],
    ):
        tags = list(DEFAULT_HASHTAGS)
        if hashtags:
            tags = hashtags
        cta = DEFAULT_CTA
        caption = (
            f"✨ {vehicle.vehicle_name or 'Pre-owned car'} is ready!\n"
            f"{self._ai_fields_text(vehicle)}\n\n"
            f"📍 {vehicle.location or 'KM Car Deals'}\n{cta}"
        )

        if ai_provider.name != "disabled":
            try:
                from km_car_deals.ai.prompts import SOCIAL_CAPTION_PROMPT
                import json, re

                raw = ai_provider.complete_llm(
                    SOCIAL_CAPTION_PROMPT.format(
                        vehicle_info=self._ai_fields_text(vehicle)
                    )
                )
                m = re.search(r"\{.*\}", raw, re.S)
                if m:
                    data = json.loads(m.group(0))
                    caption = data.get("caption", caption)
                    if data.get("hashtags"):
                        tags = data["hashtags"]
                    if data.get("cta"):
                        cta = data["cta"]
            except Exception:
                logger.exception("AI caption generation failed; using deterministic draft")

        if caption_override:
            caption = caption_override
        return caption, caption, tags, cta

    def _ai_fields_text(self, vehicle: Vehicle) -> str:
        parts = []
        if vehicle.manufacturing_year:
            parts.append(f"Year: {vehicle.manufacturing_year}")
        if vehicle.fuel_type:
            parts.append(f"Fuel: {vehicle.fuel_type}")
        if vehicle.transmission:
            parts.append(f"Transmission: {vehicle.transmission}")
        if vehicle.mileage_km:
            parts.append(f"Mileage: {vehicle.mileage_km:,} km")
        if vehicle.owner_count is not None:
            parts.append(f"Owner: {vehicle.owner_count}")
        if vehicle.selling_price:
            parts.append(f"Price: ₹{vehicle.selling_price:,.0f}")
        return "\n".join(parts)

    def _format_photo_order(self, vehicle: Vehicle) -> List[str]:
        photos = sorted(
            (p for p in vehicle.photos if p.variant in ("web", "processed") and p.category),
            key=lambda p: (not p.is_primary, p.sort_order),
        )
        category_priority = {
            "front": 0, "rear": 1, "left": 2, "right": 3, "interior": 4,
            "dashboard": 5, "boot": 6, "wheel": 7, "engine": 8,
        }
        photos.sort(key=lambda p: category_priority.get(p.category, 90))
        return [p.photo_id for p in photos[:10]]

    def approve(self, content_id: str, approved_by: str) -> Optional[SocialContent]:
        content = self.db.get(SocialContent, content_id)
        if not content:
            return None
        content.status = SocialContentStatus.APPROVED.value
        content.approved_by = approved_by
        self.db.flush()
        return content

    async def publish(self, content: SocialContent) -> dict:
        """Publish an APPROVED content item via official Meta Graph API."""
        if content.status != SocialContentStatus.APPROVED.value:
            return {"published": False, "reason": "not_approved"}
        if not (settings.INSTAGRAM_BUSINESS_ACCOUNT_ID and settings.INSTAGRAM_ACCESS_TOKEN):
            content.status = SocialContentStatus.PENDING_APPROVAL.value
            self.db.flush()
            return {"published": False, "reason": "instagram_not_configured"}
        try:
            from km_car_deals.integrations.instagram.client import InstagramClient

            ig = InstagramClient(
                business_account_id=settings.INSTAGRAM_BUSINESS_ACCOUNT_ID,
                access_token=settings.INSTAGRAM_ACCESS_TOKEN,
            )
            media_ids = await self._upload_media(ig, content)
            result = await ig.create_carousel(media_ids, content.caption)
            content.status = SocialContentStatus.PUBLISHED.value
            content.published_at = datetime.now(timezone.utc)
            content.meta_container_id = result.get("id")
            self.db.flush()
            return {"published": True, "response": result}
        except Exception as exc:
            content.last_error = str(exc)
            content.status = SocialContentStatus.FAILED.value
            self.db.flush()
            return {"published": False, "reason": str(exc)}

    async def _upload_media(self, ig, content: SocialContent) -> List[str]:
        # photo_order holds photo_ids; resolve to file paths
        media_ids = []
        from km_car_deals.models.vehicle import VehiclePhoto

        for i, photo_id in enumerate(content.photo_order or []):
            photo = self.db.get(VehiclePhoto, photo_id)
            if not photo:
                continue
            m = await ig.upload_image_media(photo.file_path, caption=content.caption if i == 0 else "")
            if m.get("id"):
                media_ids.append(m["id"])
        return media_ids
