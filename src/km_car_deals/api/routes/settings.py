"""Business settings and audit log API routes."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from km_car_deals.db.session import get_db
from km_car_deals.services import business_settings as biz_svc
from km_car_deals.services import audit as audit_svc

router = APIRouter(prefix="/settings", tags=["settings"])


class BusinessSettingsUpdate(BaseModel):
    business_name: Optional[str] = None
    tagline: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    whatsapp_number: Optional[str] = None
    email: Optional[str] = None
    website_url: Optional[str] = None
    google_maps_url: Optional[str] = None
    auto_publish: Optional[bool] = None
    default_location: Optional[str] = None
    currency: Optional[str] = None
    updated_by: str = "admin"


@router.get("/business")
def get_business_settings(db: Session = Depends(get_db)):
    """Return current dealer / business configuration."""
    row = biz_svc.get_settings(db)
    return {
        "setting_id": row.setting_id,
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


@router.patch("/business")
def update_business_settings(payload: BusinessSettingsUpdate, db: Session = Depends(get_db)):
    """Update dealer / business configuration."""
    data = payload.model_dump(exclude={"updated_by"}, exclude_none=True)
    row = biz_svc.update_settings(db, data, actor=payload.updated_by)
    db.commit()
    return {"status": "updated", "business_name": row.business_name}


@router.get("/audit-log")
def get_audit_log(
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    actor: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Retrieve audit log entries with optional filters."""
    logs = audit_svc.get_logs(
        db, entity_id=entity_id, entity_type=entity_type,
        action=action, actor=actor, limit=limit
    )
    return [
        {
            "log_id": l.log_id,
            "actor": l.actor,
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "before_data": l.before_data,
            "after_data": l.after_data,
            "notes": l.notes,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in logs
    ]
