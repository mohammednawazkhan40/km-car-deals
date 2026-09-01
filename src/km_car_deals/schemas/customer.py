"""Customer CRM-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    name: Optional[str] = None
    phone_number: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    preferred_vehicle: Optional[str] = None
    budget_min: Optional[Decimal] = None
    budget_max: Optional[Decimal] = None
    lead_status: str
    opt_in: bool = False
    opt_out: bool = False


class CustomerFollowupCreate(BaseModel):
    customer_id: str
    vehicle_id: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    reason: Optional[str] = None
    preferred_channel: Optional[str] = "WHATSAPP"
    message_template: Optional[str] = None


class FollowupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    followup_id: str
    customer_id: str
    vehicle_id: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    reason: Optional[str] = None
    status: str
    preferred_channel: Optional[str] = None


class HandoffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    customer_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    reason: str
    summary: Optional[str] = None
    status: str
    assigned_to: Optional[str] = None
