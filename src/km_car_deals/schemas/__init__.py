"""Pydantic response/request schemas."""

from km_car_deals.schemas.vehicle import (
    ConflictCreate,
    ConflictResolve,
    FactOut,
    IntakeResult,
    PublicVehicleOut,
    VehicleCreate,
    VehicleFactIn,
    VehicleOut,
    VehicleStatusUpdate,
)
from km_car_deals.schemas.customer import (
    CustomerFollowupCreate,
    CustomerOut,
    FollowupOut,
    HandoffOut,
)

__all__ = [
    "ConflictCreate",
    "ConflictResolve",
    "FactOut",
    "IntakeResult",
    "PublicVehicleOut",
    "VehicleCreate",
    "VehicleFactIn",
    "VehicleOut",
    "VehicleStatusUpdate",
    "CustomerFollowupCreate",
    "CustomerOut",
    "FollowupOut",
    "HandoffOut",
]
