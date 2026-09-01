"""Vehicle inventory database models.

Table groups:
- vehicles / vehicle_facts (fields with value/source/confidence/needs_review)
- vehicle_photos
- vehicle_documents
- vehicle_conflicts
- vehicle_listings
- vehicle_publications
- vehicle_status_history
- vehicle_audit_logs
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from km_car_deals.db.session import Base
from km_car_deals.db.types import JsonType
from km_car_deals.models.enums import (
    BodyType,
    ConflictStatus,
    DocumentType,
    FuelType,
    PhotoCategory,
    PhotoVariant,
    PublicationChannel,
    PublicationStatus,
    SourceType,
    Transmission,
    VehicleListingStatus,
    VehicleStatus,
)


def gen_uuid() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"

    vehicle_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    stock_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Core identifying fields (mirror the fact table for easy querying)
    registration_number: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)
    stock_internal: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    model: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    variant: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    vehicle_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    registration_state: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    registration_city: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    manufacturing_month: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    manufacturing_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    registration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fuel_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    transmission: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    vehicle_color: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    body_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    owner_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    owner_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    engine_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    chassis_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    vehicle_class: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    seating_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mileage_km: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    purchase_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    selling_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    condition: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    service_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    insurance_valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    puc_valid_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    features: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), default=VehicleStatus.NEW.value, index=True
    )

    # ---- Intake / workflow fields ----
    referral: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    intake_source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    dealer_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    dealer_phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    dealer_city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    intake_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # ---- Approval workflow fields ----
    approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ---- AI extraction confidence summary ----
    ai_confidence_summary: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)

    # Relationships
    facts: Mapped[list["VehicleFact"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", lazy="selectin"
    )
    photos: Mapped[list["VehiclePhoto"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", lazy="selectin"
    )
    documents: Mapped[list["VehicleDocument"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", lazy="selectin"
    )
    conflicts: Mapped[list["VehicleConflict"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", lazy="selectin"
    )
    status_history: Mapped[list["VehicleStatusHistory"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", lazy="selectin"
    )
    listings: Mapped[list["VehicleListing"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", lazy="selectin"
    )
    publications: Mapped[list["VehiclePublication"]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan", lazy="selectin"
    )


class VehicleFact(Base, TimestampMixin):
    """A single extracted/known vehicle attribute with provenance.

    Every field carries:
      value, source, confidence, needs_review
    """

    __tablename__ = "vehicle_facts"
    __table_args__ = (UniqueConstraint("vehicle_id", "field", name="uq_vehicle_fact_field"),)

    fact_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), index=True
    )
    field: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default=SourceType.RC.value)
    confidence: Mapped[float] = mapped_column(default=0.0)
    needs_review: Mapped[bool] = mapped_column(default=False)

    vehicle: Mapped[Vehicle] = relationship(back_populates="facts")


class VehiclePhoto(Base, TimestampMixin):
    __tablename__ = "vehicle_photos"

    photo_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), index=True
    )
    variant: Mapped[str] = mapped_column(String(32), default=PhotoVariant.ORIGINAL.value)
    category: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    file_path: Mapped[str] = mapped_column(String(512))
    original_file_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False)
    sort_order: Mapped[int] = mapped_column(default=0)

    # Vision analysis results
    quality_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    blur_detected: Mapped[Optional[bool]] = mapped_column(nullable=True)
    lighting_ok: Mapped[Optional[bool]] = mapped_column(nullable=True)
    composed_ok: Mapped[Optional[bool]] = mapped_column(nullable=True)
    duplicate_of: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    damage_found: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    analysis_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vehicle: Mapped[Vehicle] = relationship(back_populates="photos")


class VehicleDocument(Base, TimestampMixin):
    __tablename__ = "vehicle_documents"

    document_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), index=True
    )
    doc_type: Mapped[str] = mapped_column(String(32), default=DocumentType.OTHER.value)
    file_path: Mapped[str] = mapped_column(String(512))
    original_file_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extraction_engine: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    vehicle: Mapped[Vehicle] = relationship(back_populates="documents")


class VehicleConflict(Base, TimestampMixin):
    __tablename__ = "vehicle_conflicts"

    conflict_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), index=True
    )
    field: Mapped[str] = mapped_column(String(64))
    source_a: Mapped[str] = mapped_column(String(32))
    value_a: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_b: Mapped[str] = mapped_column(String(32))
    value_b: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=ConflictStatus.OPEN.value)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    vehicle: Mapped[Vehicle] = relationship(back_populates="conflicts")


class VehicleStatusHistory(Base, TimestampMixin):
    __tablename__ = "vehicle_status_history"

    history_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), index=True
    )
    from_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32))
    changed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    vehicle: Mapped[Vehicle] = relationship(back_populates="status_history")


class VehicleListing(Base, TimestampMixin):
    """A marketplace listing created from a vehicle."""

    __tablename__ = "vehicle_listings"

    listing_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), index=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=VehicleListingStatus.DRAFT.value
    )
    catalog_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    vehicle: Mapped[Vehicle] = relationship(back_populates="listings")


class VehiclePublication(Base, TimestampMixin):
    """Tracks where/when a vehicle was published to a channel."""

    __tablename__ = "vehicle_publications"

    publication_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[str] = mapped_column(String(32), default=PublicationChannel.WEBSITE.value)
    status: Mapped[str] = mapped_column(
        String(32), default=PublicationStatus.DRAFT.value
    )
    remote_ref: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    vehicle: Mapped[Vehicle] = relationship(back_populates="publications")


class VehicleAuditLog(Base, TimestampMixin):
    __tablename__ = "vehicle_audit_logs"

    audit_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    vehicle_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="SET NULL"), index=True, nullable=True
    )
    actor: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(128))
    detail: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)


class UploadedFileRecord(Base, TimestampMixin):
    """Tracks files received at intake before being associated to a vehicle."""

    __tablename__ = "uploaded_file_records"

    file_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    original_name: Mapped[str] = mapped_column(String(256))
    stored_path: Mapped[str] = mapped_column(String(512))
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    classification: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    doc_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    intake_batch: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class BusinessSettings(Base, TimestampMixin):
    """Configurable dealer/business settings — never hard-coded in application code."""

    __tablename__ = "business_settings"

    setting_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    business_name: Mapped[str] = mapped_column(String(256), default="KM Car Deals")
    tagline: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    phone_primary: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    phone_secondary: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    whatsapp_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    google_maps_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    auto_publish: Mapped[bool] = mapped_column(Boolean, default=False)
    default_location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    extra: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)


class AppAuditLog(Base, TimestampMixin):
    """Application-wide audit log for all AI and dealer actions."""

    __tablename__ = "app_audit_logs"

    log_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    actor: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    before_data: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    after_data: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

