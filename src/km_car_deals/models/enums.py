"""Enumerations used across the domain models."""

from __future__ import annotations

import enum


class VehicleStatus(str, enum.Enum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    PENDING_REVIEW = "PENDING_REVIEW"
    READY_FOR_SALE = "READY_FOR_SALE"
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    NEGOTIATION = "NEGOTIATION"
    SOLD = "SOLD"
    EXCHANGED = "EXCHANGED"
    PURCHASED = "PURCHASED"
    DELIVERED = "DELIVERED"
    ARCHIVED = "ARCHIVED"


# Statuses for which a vehicle is actively for sale.
ACTIVE_SALE_STATUSES = {
    VehicleStatus.AVAILABLE,
    VehicleStatus.NEGOTIATION,
    VehicleStatus.RESERVED,
    VehicleStatus.READY_FOR_SALE,
}

# Statuses that must never be advertised.
NON_ACTIVE_SALE_STATUSES = {
    VehicleStatus.SOLD,
    VehicleStatus.EXCHANGED,
    VehicleStatus.PURCHASED,
    VehicleStatus.DELIVERED,
    VehicleStatus.ARCHIVED,
}


class FuelType(str, enum.Enum):
    PETROL = "PETROL"
    DIESEL = "DIESEL"
    CNG = "CNG"
    LPG = "LPG"
    ELECTRIC = "ELECTRIC"
    HYBRID = "HYBRID"
    UNKNOWN = "UNKNOWN"


class Transmission(str, enum.Enum):
    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"
    AMT = "AMT"
    DCT = "DCT"
    CVT = "CVT"
    UNKNOWN = "UNKNOWN"


class BodyType(str, enum.Enum):
    HATCHBACK = "HATCHBACK"
    SEDAN = "SEDAN"
    SUV = "SUV"
    MPV = "MPV"
    COUPE = "COUPE"
    CONVERTIBLE = "CONVERTIBLE"
    WAGON = "WAGON"
    PICKUP = "PICKUP"
    LUXURY = "LUXURY"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class PhotoCategory(str, enum.Enum):
    FRONT = "front"
    REAR = "rear"
    LEFT = "left"
    RIGHT = "right"
    INTERIOR = "interior"
    DASHBOARD = "dashboard"
    ODOMETER = "odometer"
    ENGINE = "engine"
    BOOT = "boot"
    WHEEL = "wheel"
    TYRE = "tyre"
    OTHER = "other"


class DocumentType(str, enum.Enum):
    RC = "RC"
    INSURANCE = "INSURANCE"
    PUC = "PUC"
    SERVICE = "SERVICE"
    INVOICE = "INVOICE"
    OTHER = "OTHER"


class PhotoVariant(str, enum.Enum):
    ORIGINAL = "original"
    PROCESSED = "processed"
    WEB = "web"
    SOCIAL = "social"
    THUMBNAIL = "thumbnail"


class ConflictStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"


class VehicleListingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    PUBLISHED = "PUBLISHED"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    REMOVED = "REMOVED"


class PublicationChannel(str, enum.Enum):
    WHATSAPP = "WHATSAPP"
    WEBSITE = "WEBSITE"
    INSTAGRAM = "INSTAGRAM"
    EXCEL = "EXCEL"


class PublicationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    REMOVED = "REMOVED"


class LeadStatus(str, enum.Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    INTERESTED = "INTERESTED"
    QUALIFIED = "QUALIFIED"
    NEGOTIATING = "NEGOTIATING"
    FOLLOW_UP = "FOLLOW_UP"
    BOOKED = "BOOKED"
    PURCHASED = "PURCHASED"
    LOST = "LOST"
    NOT_INTERESTED = "NOT_INTERESTED"


class InterestType(str, enum.Enum):
    VIEWED = "VIEWED"
    ENQUIRED = "ENQUIRED"
    TEST_DRIVE = "TEST_DRIVE"
    BOOKED = "BOOKED"


class InterestStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FOLLOW_UP = "FOLLOW_UP"
    CONVERTED = "CONVERTED"
    LOST = "LOST"


class InteractionType(str, enum.Enum):
    INBOUND_MESSAGE = "INBOUND_MESSAGE"
    OUTBOUND_MESSAGE = "OUTBOUND_MESSAGE"
    CALL = "CALL"
    SHOWROOM_VISIT = "SHOWROOM_VISIT"
    TEST_DRIVE = "TEST_DRIVE"
    EMAIL = "EMAIL"
    NOTE = "NOTE"


class FollowupReason(str, enum.Enum):
    NEW_LEAD = "NEW_LEAD"
    PRICE_DISCUSSION = "PRICE_DISCUSSION"
    VEHICLE_INTEREST = "VEHICLE_INTEREST"
    SHOWROOM_VISIT = "SHOWROOM_VISIT"
    TEST_DRIVE = "TEST_DRIVE"
    DOCUMENT_PENDING = "DOCUMENT_PENDING"
    NEGOTIATION = "NEGOTIATION"
    BOOKING = "BOOKING"
    PAYMENT = "PAYMENT"
    DELIVERY = "DELIVERY"
    POST_SALE = "POST_SALE"
    CUSTOMER_DECISION = "CUSTOMER_DECISION"
    CALL_REQUEST = "CALL_REQUEST"


class FollowupStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class ContactChannel(str, enum.Enum):
    WHATSAPP = "WHATSAPP"
    CALL = "CALL"
    EMAIL = "EMAIL"
    SMS = "SMS"


class ConsentStatus(str, enum.Enum):
    OPTED_IN = "OPTED_IN"
    OPTED_OUT = "OPTED_OUT"
    UNKNOWN = "UNKNOWN"


class HumanHandoffStatus(str, enum.Enum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class HandoffReason(str, enum.Enum):
    ANGRY_CUSTOMER = "ANGRY_CUSTOMER"
    PRICE_NEGOTIATION = "PRICE_NEGOTIATION"
    LARGE_DISCOUNT_REQUEST = "LARGE_DISCOUNT_REQUEST"
    LEGAL_QUESTION = "LEGAL_QUESTION"
    FINANCING_APPROVAL = "FINANCING_APPROVAL"
    PAYMENT_ISSUE = "PAYMENT_ISSUE"
    COMPLAINT = "COMPLAINT"
    BOOKING_CONFIRMATION = "BOOKING_CONFIRMATION"
    DOCUMENT_DISPUTE = "DOCUMENT_DISPUTE"
    VEHICLE_CONDITION_DISPUTE = "VEHICLE_CONDITION_DISPUTE"
    OTHER = "OTHER"


class CatalogEntryStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    PUBLISHED = "PUBLISHED"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    REMOVED = "REMOVED"


class SocialContentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class SourceType(str, enum.Enum):
    RC = "RC"
    USER = "user"
    DATABASE = "database"
    EXCEL = "excel"
    PHOTO = "photo"
