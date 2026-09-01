"""Public website inventory API - exposes only safe fields."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from km_car_deals.core.config import settings
from km_car_deals.db.session import get_db
from km_car_deals.schemas.vehicle import PublicVehicleOut
from km_car_deals.services import inventory

router = APIRouter(prefix="/public", tags=["public"])


def _require_public_key(public_api_key: Optional[str]) -> None:
    if settings.PUBLIC_API_REQUIRES_KEY:
        if not public_api_key or public_api_key != settings.PUBLIC_API_KEY:
            raise HTTPException(401, "Invalid or missing public API key")


@router.get("/vehicles", response_model=List[PublicVehicleOut])
def list_public_vehicles(
    fuel: Optional[str] = None,
    transmission: Optional[str] = None,
    body_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    vehicles = inventory.search_vehicles(
        db,
        fuel=fuel,
        transmission=transmission,
        body_type=body_type,
        min_price=min_price,
        max_price=max_price,
        brand=brand,
        model=model,
        q=q,
        active_only=True,
        limit=limit,
    )
    return [inventory.public_vehicle_out(v) for v in vehicles]


@router.get("/vehicles/{stock_id}", response_model=PublicVehicleOut)
def get_public_vehicle(stock_id: str, db: Session = Depends(get_db)):
    v = inventory.get_vehicle_by_stock(db, stock_id)
    if not v or not inventory.vehicle_is_active(v):
        raise HTTPException(404, "Vehicle not found")
    return inventory.public_vehicle_out(v)


@router.get("/vehicles/search/ai")
def ai_search(db: Session = Depends(get_db)):
    """Endpoint that accepts structured filter params from a website AI search.

    The website frontend converts NL queries to structured filters server-side
    (the LLM never runs arbitrary SQL). This endpoint mirrors list_public_vehicles.
    """
    return {"message": "Use structured query params on /public/vehicles"}
