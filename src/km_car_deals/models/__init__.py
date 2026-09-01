"""ORM model package - imports all models so Alembic autogenerate can see them."""

from km_car_deals.models.vehicle import (
    UploadedFileRecord,
    Vehicle,
    VehicleAuditLog,
    VehicleConflict,
    VehicleDocument,
    VehicleFact,
    VehicleListing,
    VehiclePhoto,
    VehiclePublication,
    VehicleStatusHistory,
)
from km_car_deals.models.customer import (
    Customer,
    CustomerConsent,
    CustomerContact,
    CustomerFollowup,
    CustomerInteraction,
    CustomerLead,
    CustomerMessage,
    CustomerNote,
    CustomerPreference,
    CustomerVehicleInterest,
    HumanHandoffTask,
)
from km_car_deals.models.catalog import SocialContent, WhatsAppCatalogEntry

__all__ = [
    "UploadedFileRecord",
    "Vehicle",
    "VehicleAuditLog",
    "VehicleConflict",
    "VehicleDocument",
    "VehicleFact",
    "VehicleListing",
    "VehiclePhoto",
    "VehiclePublication",
    "VehicleStatusHistory",
    "Customer",
    "CustomerConsent",
    "CustomerContact",
    "CustomerFollowup",
    "CustomerInteraction",
    "CustomerLead",
    "CustomerMessage",
    "CustomerNote",
    "CustomerPreference",
    "CustomerVehicleInterest",
    "HumanHandoffTask",
    "SocialContent",
    "WhatsAppCatalogEntry",
]
