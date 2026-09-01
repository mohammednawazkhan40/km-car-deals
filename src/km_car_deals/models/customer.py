"""Customer CRM database models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from km_car_deals.db.session import Base
from km_car_deals.db.types import JsonType
from km_car_deals.models.enums import ConsentStatus, ContactChannel, LeadStatus
from km_car_deals.models.vehicle import TimestampMixin, gen_uuid


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    whatsapp_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(256), nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    preferred_language: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    preferred_vehicle: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    budget_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    budget_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    fuel_preference: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    transmission_preference: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    color_preference: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    purchase_timeline: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lead_status: Mapped[str] = mapped_column(
        String(32), default=LeadStatus.NEW.value, index=True
    )

    # WhatsApp policy / consent
    opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    opt_out: Mapped[bool] = mapped_column(Boolean, default=False)
    opt_out_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    consent_status: Mapped[str] = mapped_column(
        String(32), default=ConsentStatus.UNKNOWN.value
    )
    last_inbound_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_outbound_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    conversation_window_open: Mapped[bool] = mapped_column(Boolean, default=False)

    contacts: Mapped[list["CustomerContact"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    preferences: Mapped[list["CustomerPreference"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    leads: Mapped[list["CustomerLead"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    interactions: Mapped[list["CustomerInteraction"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    followups: Mapped[list["CustomerFollowup"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    interests: Mapped[list["CustomerVehicleInterest"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    messages: Mapped[list["CustomerMessage"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )
    consents: Mapped[list["CustomerConsent"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan", lazy="selectin"
    )


class CustomerContact(Base, TimestampMixin):
    __tablename__ = "customer_contacts"

    contact_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="CASCADE"), index=True
    )
    channel: Mapped[str] = mapped_column(String(32), default=ContactChannel.WHATSAPP.value)
    value: Mapped[str] = mapped_column(String(256))
    is_primary: Mapped[bool] = mapped_column(default=False)

    customer: Mapped[Customer] = relationship(back_populates="contacts")


class CustomerPreference(Base, TimestampMixin):
    __tablename__ = "customer_preferences"

    preference_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(64))
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="preferences")


class CustomerLead(Base, TimestampMixin):
    __tablename__ = "customer_leads"

    lead_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="CASCADE"), index=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default=LeadStatus.NEW.value, index=True
    )
    channel: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="leads")


class CustomerInteraction(Base, TimestampMixin):
    __tablename__ = "customer_interactions"

    interaction_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="CASCADE"), index=True
    )
    vehicle_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="SET NULL"), nullable=True, index=True
    )
    interaction_type: Mapped[str] = mapped_column(String(32))
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    interaction_metadata: Mapped[Optional[dict]] = mapped_column(JsonType, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="interactions")


class CustomerFollowup(Base, TimestampMixin):
    __tablename__ = "customer_followups"

    followup_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="CASCADE"), index=True
    )
    vehicle_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="SET NULL"), nullable=True, index=True
    )
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    last_contacted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    customer_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_channel: Mapped[Optional[str]] = mapped_column(
        String(32), default=ContactChannel.WHATSAPP.value
    )
    message_template: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="followups")


class CustomerVehicleInterest(Base, TimestampMixin):
    __tablename__ = "customer_vehicle_interest"

    interest_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="CASCADE"), index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), index=True
    )
    interest_type: Mapped[str] = mapped_column(String(32), default="ENQUIRED")
    interest_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_contacted: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_followup: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    interest_status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="interests")


class CustomerMessage(Base, TimestampMixin):
    __tablename__ = "customer_messages"
    __table_args__ = (
        UniqueConstraint("message_id", name="uq_customer_message_msg"),
    )

    message_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="CASCADE"), index=True
    )
    direction: Mapped[str] = mapped_column(String(16))
    channel: Mapped[str] = mapped_column(String(32), default="WHATSAPP")
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    meta_message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    template_used: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="messages")


class CustomerNote(Base, TimestampMixin):
    __tablename__ = "customer_notes"

    note_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="CASCADE"), index=True
    )
    author: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship()


class CustomerConsent(Base, TimestampMixin):
    __tablename__ = "customer_consents"

    consent_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="CASCADE"), index=True
    )
    purpose: Mapped[str] = mapped_column(String(64), default="MARKETING")
    status: Mapped[str] = mapped_column(
        String(32), default=ConsentStatus.UNKNOWN.value
    )
    channel: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    customer: Mapped[Customer] = relationship(back_populates="consents")


class HumanHandoffTask(Base, TimestampMixin):
    __tablename__ = "human_handoff_tasks"

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=gen_uuid)
    customer_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="SET NULL"), nullable=True, index=True
    )
    vehicle_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("vehicles.vehicle_id", ondelete="SET NULL"), nullable=True, index=True
    )
    reason: Mapped[str] = mapped_column(String(64), default="OTHER")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    assigned_to: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    channel: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

