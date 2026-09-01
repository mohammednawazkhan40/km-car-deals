"""Vehicle inventory API routes (internal, authenticated)."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from km_car_deals.db.session import get_db
from km_car_deals.schemas.vehicle import (
    ConflictResolve,
    IntakeResult,
    VehicleOut,
    VehicleStatusUpdate,
)
from km_car_deals.services import inventory

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=List[VehicleOut])
def list_vehicles(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    fuel: Optional[str] = None,
    status: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    vehicles = inventory.search_vehicles(
        db,
        brand=brand,
        model=model,
        fuel=fuel,
        status=status,
        active_only=active_only,
    )
    return vehicles


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    v = inventory.get_vehicle(db, vehicle_id)
    if not v:
        raise HTTPException(404, "Vehicle not found")
    return v


@router.post("/{vehicle_id}/status", response_model=VehicleOut)
def set_status(vehicle_id: str, payload: VehicleStatusUpdate, db: Session = Depends(get_db)):
    try:
        v = inventory.update_status(
            db, vehicle_id, payload.status.upper(), reason=payload.reason, actor="api"
        )
    except KeyError:
        raise HTTPException(404, "Vehicle not found")
    from km_car_deals.services import catalog

    catalog.handle_vehicle_status_change(db, vehicle_id)
    db.commit()
    return v


@router.get("/{vehicle_id}/conflicts")
def list_conflicts(vehicle_id: str, db: Session = Depends(get_db)):
    return inventory.open_conflicts(db, vehicle_id)


@router.post("/{vehicle_id}/conflicts/{conflict_id}/resolve")
def resolve_conflict(
    vehicle_id: str, conflict_id: str, payload: ConflictResolve, db: Session = Depends(get_db)
):
    resolved = inventory.resolve_conflict(
        db, vehicle_id, conflict_id, payload.resolution_value, resolved_by=payload.resolved_by
    )
    if not resolved:
        raise HTTPException(404, "Conflict not found")
    v = inventory.sync_vehicle_from_facts(db, vehicle_id)
    db.commit()
    return {"status": "resolved", "vehicle_id": vehicle_id, "value": payload.resolution_value}
