"""BusinessSettings service — single-row dealer configuration.

Never hard-codes business information. Everything is stored in the
business_settings table and seeded from env vars on first run.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from km_car_deals.core.config import settings
from km_car_deals.core.logging import get_logger
from km_car_deals.models.vehicle import BusinessSettings

logger = get_logger(__name__)


def get_settings(db: Session) -> BusinessSettings:
    """Return the single BusinessSettings row, creating and seeding it if absent."""
    row = db.execute(select(BusinessSettings)).scalars().first()
    if row is None:
        row = _seed(db)
    return row


def update_settings(db: Session, data: dict, actor: str = "admin") -> BusinessSettings:
    """Update business settings from a dict payload."""
    from km_car_deals.services.audit import log_action

    row = get_settings(db)
    before = _to_dict(row)
    allowed = {
        "business_name", "tagline", "address_line1", "address_line2", "city", "state",
        "pincode", "phone_primary", "phone_secondary", "whatsapp_number", "email",
        "website_url", "google_maps_url", "auto_publish", "default_location",
        "currency", "extra",
    }
    for key, val in data.items():
        if key in allowed and val is not None:
            setattr(row, key, val)
    db.flush()
    log_action(db, actor=actor, action="UPDATE_BUSINESS_SETTINGS",
               entity_type="BusinessSettings", entity_id=row.setting_id,
               before_data=before, after_data=_to_dict(row))
    return row


def _seed(db: Session) -> BusinessSettings:
    """Seed from env vars (called once on first access)."""
    row = BusinessSettings(
        business_name=settings.DEALER_NAME,
        tagline=settings.DEALER_TAGLINE,
        address_line1=settings.DEALER_ADDRESS_LINE1,
        address_line2=settings.DEALER_ADDRESS_LINE2,
        city=settings.DEALER_CITY,
        state=settings.DEALER_STATE,
        pincode=settings.DEALER_PINCODE,
        phone_primary=settings.DEALER_PHONE_PRIMARY or None,
        phone_secondary=settings.DEALER_PHONE_SECONDARY or None,
        whatsapp_number=settings.DEALER_WHATSAPP or None,
        email=settings.DEALER_EMAIL or None,
        website_url=settings.DEALER_WEBSITE or None,
        google_maps_url=settings.DEALER_GOOGLE_MAPS_URL or None,
        auto_publish=settings.DEALER_AUTO_PUBLISH,
        default_location=settings.DEALER_CITY,
    )
    db.add(row)
    db.flush()
    logger.info("Seeded BusinessSettings from env vars (dealer: %s)", row.business_name)
    return row


def _to_dict(row: BusinessSettings) -> dict:
    return {
        "business_name": row.business_name,
        "tagline": row.tagline,
        "address_line1": row.address_line1,
        "address_line2": row.address_line2,
        "city": row.city,
        "state": row.state,
        "pincode": row.pincode,
        "phone_primary": row.phone_primary,
        "phone_secondary": row.phone_secondary,
        "whatsapp_number": row.whatsapp_number,
        "email": row.email,
        "website_url": row.website_url,
        "google_maps_url": row.google_maps_url,
        "auto_publish": row.auto_publish,
        "default_location": row.default_location,
        "currency": row.currency,
    }


def whatsapp_enquiry_url(db: Session, vehicle_name: str, stock_id: str) -> str:
    """Generate a WhatsApp click-to-chat URL pre-filled with vehicle enquiry."""
    biz = get_settings(db)
    number = (biz.whatsapp_number or "").strip().lstrip("+").replace(" ", "")
    if not number:
        return ""
    msg = (
        f"Hello {biz.business_name}, I am interested in the {vehicle_name} "
        f"(Stock: {stock_id}) listed on your website. "
        f"Please share availability, price and more details."
    )
    import urllib.parse
    return f"https://wa.me/{number}?text={urllib.parse.quote(msg)}"
