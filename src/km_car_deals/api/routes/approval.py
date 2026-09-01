"""Approval workflow API routes.

Handles the full dealer review → approve → publish lifecycle:
  AI_DRAFT → EXTRACTED → NEEDS_REVIEW → DEALER_APPROVED → PUBLISHED
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from km_car_deals.db.session import get_db
from km_car_deals.services import inventory, audit as audit_svc, business_settings as biz_svc
from km_car_deals.models.vehicle import Vehicle

router = APIRouter(prefix="/approval", tags=["approval"])


# ── Pydantic request bodies ────────────────────────────────────────────────


class ApproveRequest(BaseModel):
    approved_by: str = "admin"


class RejectRequest(BaseModel):
    reason: str
    rejected_by: str = "admin"


class ReprocessRequest(BaseModel):
    actor: str = "admin"


class PublishRequest(BaseModel):
    published_by: str = "admin"


class UpdateVehicleFieldsRequest(BaseModel):
    """Allow dealer to correct any extraction field before approving."""
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
    selling_price: Optional[float] = None
    location: Optional[str] = None
    body_type: Optional[str] = None
    referral: Optional[str] = None
    description: Optional[str] = None
    updated_by: str = "admin"


# ── Helpers ────────────────────────────────────────────────────────────────


def _vehicle_or_404(db: Session, vehicle_id: str) -> Vehicle:
    v = inventory.get_vehicle(db, vehicle_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return v


def _vehicle_summary(v: Vehicle) -> Dict[str, Any]:
    """Safe summary dict for API responses."""
    confidence = v.ai_confidence_summary or {}
    needs_review_fields = [
        k for k, val in confidence.items() if val.get("needs_review")
    ]
    low_confidence_fields = [
        k for k, val in confidence.items() if val.get("confidence", 1.0) < 0.7
    ]
    return {
        "vehicle_id": v.vehicle_id,
        "stock_id": v.stock_id,
        "status": v.status,
        "vehicle_name": v.vehicle_name,
        "manufacturer": v.manufacturer,
        "model": v.model,
        "variant": v.variant,
        "manufacturing_year": v.manufacturing_year,
        "fuel_type": v.fuel_type,
        "transmission": v.transmission,
        "vehicle_color": v.vehicle_color,
        "owner_count": v.owner_count,
        "mileage_km": v.mileage_km,
        "selling_price": float(v.selling_price) if v.selling_price else None,
        "location": v.location,
        "body_type": v.body_type,
        "registration_number": v.registration_number,
        "referral": v.referral,
        "description": v.description,
        "approved_by": v.approved_by,
        "approved_at": v.approved_at.isoformat() if v.approved_at else None,
        "rejected_by": v.rejected_by,
        "rejection_reason": v.rejection_reason,
        "published_at": v.published_at.isoformat() if v.published_at else None,
        "conflicts": len([c for c in v.conflicts if c.status == "OPEN"]),
        "photos": len(v.photos),
        "confidence_summary": confidence,
        "needs_review_fields": needs_review_fields,
        "low_confidence_fields": low_confidence_fields,
        "ready_for_approval": not needs_review_fields and not low_confidence_fields and not v.conflicts,
        "facts": [
            {
                "field": f.field,
                "value": f.value,
                "source": f.source,
                "confidence": f.confidence,
                "needs_review": f.needs_review,
            }
            for f in sorted(v.facts, key=lambda x: -x.confidence)
        ],
        "photos_detail": [
            {
                "photo_id": p.photo_id,
                "file_path": p.file_path,
                "variant": p.variant,
                "category": p.category,
                "is_primary": p.is_primary,
                "sort_order": p.sort_order,
                "quality_score": p.quality_score,
                "blur_detected": p.blur_detected,
                "duplicate_of": p.duplicate_of,
            }
            for p in sorted(v.photos, key=lambda x: (not x.is_primary, x.sort_order))
        ],
        "status_history": [
            {"from": h.from_status, "to": h.to_status, "by": h.changed_by, "reason": h.reason,
             "at": h.created_at.isoformat() if h.created_at else None}
            for h in v.status_history
        ],
    }


# ── Routes ─────────────────────────────────────────────────────────────────


@router.get("/pending")
def list_pending(
    statuses: str = Query("AI_DRAFT,EXTRACTED,NEEDS_REVIEW,DEALER_APPROVED"),
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List vehicles awaiting dealer review or approval."""
    status_list = [s.strip() for s in statuses.split(",") if s.strip()]
    results = []
    for status in status_list:
        results.extend(inventory.search_vehicles(db, status=status, active_only=False, limit=limit))
    # deduplicate preserving order
    seen: set[str] = set()
    unique = []
    for v in results:
        if v.vehicle_id not in seen:
            seen.add(v.vehicle_id)
            unique.append(v)
    return [_vehicle_summary(v) for v in unique[:limit]]


@router.get("/{vehicle_id}")
def get_review(vehicle_id: str, db: Session = Depends(get_db)):
    """Full approval review payload for a vehicle — RC, facts, confidence, photos."""
    v = _vehicle_or_404(db, vehicle_id)
    return _vehicle_summary(v)


@router.patch("/{vehicle_id}/fields")
def update_fields(
    vehicle_id: str,
    payload: UpdateVehicleFieldsRequest,
    db: Session = Depends(get_db),
):
    """Dealer corrects extracted fields before approving."""
    from km_car_deals.schemas.vehicle import VehicleFactIn

    v = _vehicle_or_404(db, vehicle_id)
    before = {"status": v.status}
    field_map = {
        "manufacturer": "manufacturer", "model": "model", "variant": "variant",
        "vehicle_name": "vehicle_name", "manufacturing_year": "manufacturing_year",
        "fuel_type": "fuel_type", "transmission": "transmission",
        "vehicle_color": "vehicle_color", "owner_count": "owner_count",
        "mileage_km": "mileage_km", "selling_price": "selling_price",
        "location": "location", "body_type": "body_type", "description": "description",
        "referral": "referral",
    }
    updated: List[str] = []
    for attr, col in field_map.items():
        val = getattr(payload, attr, None)
        if val is not None:
            setattr(v, col, val)
            # write as user fact for traceability
            if col not in ("description", "referral", "body_type"):
                inventory.set_fact(db, vehicle_id, VehicleFactIn(
                    field=col, value=str(val), source="user", confidence=1.0, needs_review=False,
                ))
            updated.append(col)

    if updated:
        audit_svc.log_action(db, actor=payload.updated_by, action="VEHICLE_FIELDS_UPDATED",
                             entity_type="Vehicle", entity_id=vehicle_id,
                             before_data=before, after_data={"updated_fields": updated})
        inventory.sync_vehicle_from_facts(db, vehicle_id)
        # Regenerate description if it was overwritten or is now stale
        if "description" not in updated and v.status in ("AI_DRAFT", "EXTRACTED", "NEEDS_REVIEW"):
            v.description = inventory.generate_description(v)
        db.commit()

    return _vehicle_summary(v)


@router.post("/{vehicle_id}/approve")
def approve_vehicle(
    vehicle_id: str, payload: ApproveRequest, db: Session = Depends(get_db)
):
    """Approve a vehicle — moves to DEALER_APPROVED, generates description."""
    try:
        v = inventory.approve_vehicle(db, vehicle_id, approved_by=payload.approved_by)
    except KeyError:
        raise HTTPException(404, "Vehicle not found")
    db.commit()
    return _vehicle_summary(v)


@router.post("/{vehicle_id}/reject")
def reject_vehicle(
    vehicle_id: str, payload: RejectRequest, db: Session = Depends(get_db)
):
    """Reject a vehicle back to NEEDS_REVIEW with a reason."""
    try:
        v = inventory.reject_vehicle(db, vehicle_id, reason=payload.reason, rejected_by=payload.rejected_by)
    except KeyError:
        raise HTTPException(404, "Vehicle not found")
    db.commit()
    return _vehicle_summary(v)


@router.post("/{vehicle_id}/reprocess")
def reprocess_vehicle(
    vehicle_id: str, payload: ReprocessRequest, db: Session = Depends(get_db)
):
    """Reset vehicle to AI_DRAFT for re-intake/reprocessing."""
    try:
        v = inventory.reprocess_vehicle(db, vehicle_id, actor=payload.actor)
    except KeyError:
        raise HTTPException(404, "Vehicle not found")
    db.commit()
    return _vehicle_summary(v)


@router.post("/{vehicle_id}/publish")
def publish_vehicle(
    vehicle_id: str, payload: PublishRequest, db: Session = Depends(get_db)
):
    """Publish a DEALER_APPROVED vehicle to the website catalog."""
    try:
        v = inventory.publish_vehicle(db, vehicle_id, published_by=payload.published_by)
    except KeyError:
        raise HTTPException(404, "Vehicle not found")
    except ValueError as e:
        raise HTTPException(400, str(e))
    from km_car_deals.services import catalog
    catalog.handle_vehicle_status_change(db, vehicle_id)
    db.commit()
    return _vehicle_summary(v)


@router.post("/{vehicle_id}/generate-description")
def generate_description(vehicle_id: str, db: Session = Depends(get_db)):
    """(Re)generate the AI listing description for a vehicle."""
    v = _vehicle_or_404(db, vehicle_id)
    desc = inventory.generate_description(v)
    v.description = desc
    audit_svc.log_action(db, actor="system", action="DESCRIPTION_GENERATED",
                         entity_type="Vehicle", entity_id=vehicle_id,
                         after_data={"description_length": len(desc)})
    db.commit()
    return {"vehicle_id": vehicle_id, "description": desc}


@router.get("/{vehicle_id}/duplicate-check")
def duplicate_check(vehicle_id: str, db: Session = Depends(get_db)):
    """Check whether this vehicle's registration number already exists."""
    v = _vehicle_or_404(db, vehicle_id)
    dups = inventory.find_possible_duplicates(
        db,
        registration_number=v.registration_number,
        chassis_number=v.chassis_number,
        manufacturer=v.manufacturer,
        model=v.model,
        year=v.manufacturing_year,
    )
    dups = [d for d in dups if d.vehicle_id != vehicle_id]
    return {
        "vehicle_id": vehicle_id,
        "duplicates_found": len(dups),
        "duplicates": [
            {"vehicle_id": d.vehicle_id, "stock_id": d.stock_id,
             "status": d.status, "registration_number": d.registration_number}
            for d in dups
        ],
    }
