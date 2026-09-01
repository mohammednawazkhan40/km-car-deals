"""Vehicle-related Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    field: str
    value: Optional[str] = None
    source: str
    confidence: float = 0.0
    needs_review: bool = False


class VehicleFactIn(BaseModel):
    field: str
    value: Optional[str] = None
    source: str = "RC"
    confidence: float = 0.0
    needs_review: bool = False


class VehiclePhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    photo_id: str
    variant: str
    category: Optional[str] = None
    file_path: str
    is_primary: bool = False
    quality_score: Optional[float] = None


class VehicleCreate(BaseModel):
    stock_id: Optional[str] = None
    registration_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    vehicle_name: Optional[str] = None
    manufacturing_year: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    vehicle_color: Optional[str] = None
    owner_count: Optional[int] = None
    mileage_km: Optional[int] = None
    selling_price: Optional[Decimal] = None
    location: Optional[str] = None
    facts: List[VehicleFactIn] = []


class VehicleStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vehicle_id: str
    stock_id: Optional[str] = None
    registration_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    vehicle_name: Optional[str] = None
    manufacturing_year: Optional[int] = None
    fuel_type: Optional[str] = None
    transmission: Optional[str] = None
    vehicle_color: Optional[str] = None
    owner_count: Optional[int] = None
    mileage_km: Optional[int] = None
    selling_price: Optional[Decimal] = None
    location: Optional[str] = None
    status: str
    facts: List[FactOut] = []
    photos: List[VehiclePhotoOut] = []


class ConflictCreate(BaseModel):
    field: str
    source_a: str
    value_a: Optional[str] = None
    source_b: str
    value_b: Optional[str] = None
    message: Optional[str] = None


class ConflictResolve(BaseModel):
    resolution_value: str
    resolved_by: Optional[str] = None


class IntakeResult(BaseModel):
    status: str
    vehicle_id: Optional[str] = None
    message: str
    conflicts_created: int = 0


class PublicVehicleOut(BaseModel):
    """Safe public view - never exposes owner/internal/private fields."""

    stock_id: Optional[str] = None
    vehicle_name: Optional[str] = None
    model: Optional[str] = None
    variant: Optional[str] = None
    year: Optional[int] = None
    fuel: Optional[str] = None
    transmission: Optional[str] = None
    color: Optional[str] = None
    mileage_km: Optional[int] = None
    price: Optional[Decimal] = None
    photos: List[str] = []
    features: Optional[list] = None
    description: Optional[str] = None
    availability: str
    location: Optional[str] = None
