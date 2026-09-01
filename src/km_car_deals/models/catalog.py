"""WhatsApp catalog & Instagram social content models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from km_car_deals.db.session import Base
from km_car_deals.db.types import JsonType
from km_car_deals.models.enums import CatalogEntryStatus, SocialContentStatus
from km_car_deals.models.vehicle import TimestampMixin, gen_uuid


class WhatsAppCatalogEntry(Base, TimestampMixin):
    __tablename__ = "whatsapp_catalog_entries"

    entry_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default=CatalogEntryStatus.DRAFT.value
    )
    sync_status: Mapped[str] = mapped_column(String(32), default="NOT_SYNCED")
    meta_product_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(8), default="INR")
    availability: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    additional_images: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    last_meta_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SocialContent(Base, TimestampMixin):
    __tablename__ = "social_content"

    content_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    vehicle_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="SET NULL"), nullable=True, index=True
    )
    platform: Mapped[str] = mapped_column(String(32), default="INSTAGRAM")
    status: Mapped[str] = mapped_column(
        String(32), default=SocialContentStatus.DRAFT.value
    )
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    cta: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    photo_order: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    media_paths: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    meta_media_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    meta_container_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

