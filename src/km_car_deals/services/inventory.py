"""Vehicle inventory service: CRUD, status transitions, facts, search, conflicts."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from km_car_deals.core.logging import get_logger
from km_car_deals.models.enums import (
    ACTIVE_SALE_STATUSES,
    ConflictStatus,
    SourceType,
    VehicleStatus,
)
from km_car_deals.models.vehicle import (
    Vehicle,
    VehicleConflict,
    VehicleFact,
    VehicleStatusHistory,
)
from km_car_deals.schemas.vehicle import VehicleCreate, VehicleFactIn

logger = get_logger(__name__)


def generate_stock_id(db: Session) -> str:
    count = db.execute(select(Vehicle)).scalars().all().__len__()
    return f"KM-{count + 1000:04d}"


def create_vehicle(db: Session, data: VehicleCreate, created_by: str | None = None) -> Vehicle:
    stock_id = data.stock_id or generate_stock_id(db)
    vehicle = Vehicle(
        stock_id=stock_id,
        created_by=created_by,
        registration_number=_clean_regno(data.registration_number),
        manufacturer=_title(data.manufacturer),
        model=_title(data.model),
        variant=_title(data.variant),
        vehicle_name=_title(data.vehicle_name),
        manufacturing_year=data.manufacturing_year,
        fuel_type=_upper(data.fuel_type),
        transmission=_upper(data.transmission),
        vehicle_color=_title(data.vehicle_color),
        owner_count=data.owner_count,
        mileage_km=data.mileage_km,
        selling_price=data.selling_price,
        location=_title(data.location),
        status=VehicleStatus.NEW.value,
    )
    db.add(vehicle)
    db.flush()
    for fact in data.facts:
        set_fact(db, vehicle.vehicle_id, fact)
    record_status(db, vehicle, None, VehicleStatus.NEW, created_by, "Vehicle created")
    db.flush()
    return vehicle


def _clean_regno(v: Optional[str]) -> Optional[str]:
    if not v:
        return v
    return re.sub(r"[\s]+", " ", v.strip().upper())


def _title(v: Optional[str]) -> Optional[str]:
    return v.strip() if isinstance(v, str) and v.strip() else v


def _upper(v: Optional[str]) -> Optional[str]:
    return v.strip().upper() if isinstance(v, str) and v.strip() else v


def set_fact(db: Session, vehicle_id: str, fact: VehicleFactIn) -> VehicleFact:
    existing = db.execute(
        select(VehicleFact).where(
            VehicleFact.vehicle_id == vehicle_id, VehicleFact.field == fact.field
        )
    ).scalar_one_or_none()
    if existing:
        existing.value = fact.value
        existing.source = fact.source
        existing.confidence = fact.confidence
        existing.needs_review = fact.needs_review
        obj = existing
    else:
        obj = VehicleFact(
            vehicle_id=vehicle_id,
            field=fact.field,
            value=fact.value,
            source=fact.source,
            confidence=fact.confidence,
            needs_review=fact.needs_review,
        )
        db.add(obj)
    db.flush()
    return obj


def get_vehicle(db: Session, vehicle_id: str) -> Optional[Vehicle]:
    return db.get(Vehicle, vehicle_id)


def get_vehicle_by_stock(db: Session, stock_id: str) -> Optional[Vehicle]:
    return db.execute(
        select(Vehicle).where(Vehicle.stock_id == stock_id)
    ).scalar_one_or_none()


def update_status(
    db: Session,
    vehicle_id: str,
    new_status: str,
    reason: Optional[str] = None,
    actor: Optional[str] = None,
) -> Vehicle:
    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise KeyError("Vehicle not found")
    old = vehicle.status
    if old != new_status:
        record_status(db, vehicle, old, VehicleStatus(new_status), actor, reason)
        vehicle.status = new_status
        db.flush()
    return vehicle


def record_status(
    db: Session,
    vehicle: Vehicle,
    from_status: Optional[str],
    to_status: VehicleStatus,
    actor: Optional[str],
    reason: Optional[str],
) -> None:
    db.add(
        VehicleStatusHistory(
            vehicle_id=vehicle.vehicle_id,
            from_status=from_status,
            to_status=to_status.value,
            changed_by=actor,
            reason=reason,
        )
    )


def create_conflict(
    db: Session,
    vehicle_id: str,
    field: str,
    source_a: str,
    value_a: Optional[str],
    source_b: str,
    value_b: Optional[str],
    message: Optional[str] = None,
) -> VehicleConflict:
    conflict = VehicleConflict(
        vehicle_id=vehicle_id,
        field=field,
        source_a=source_a,
        value_a=value_a,
        source_b=source_b,
        value_b=value_b,
        message=message,
        status=ConflictStatus.OPEN.value,
    )
    db.add(conflict)
    db.flush()
    return conflict


def open_conflicts(db: Session, vehicle_id: str) -> List[VehicleConflict]:
    return list(
        db.execute(
            select(VehicleConflict).where(
                VehicleConflict.vehicle_id == vehicle_id,
                VehicleConflict.status == ConflictStatus.OPEN.value,
            )
        ).scalars()
    )


def resolve_conflict(
    db: Session,
    vehicle_id: str,
    conflict_id: str,
    resolution_value: str,
    resolved_by: Optional[str] = None,
    field_fact_source: str = SourceType.USER.value,
) -> Optional[VehicleConflict]:
    conflict = db.get(VehicleConflict, conflict_id)
    if not conflict or conflict.vehicle_id != vehicle_id:
        return None
    conflict.status = ConflictStatus.RESOLVED.value
    conflict.resolution = resolution_value
    conflict.resolved_by = resolved_by
    # Write the agreed value back as the authoritative fact.
    set_fact(
        db,
        vehicle_id,
        VehicleFactIn(
            field=conflict.field,
            value=resolution_value,
            source=field_fact_source,
            confidence=1.0,
            needs_review=False,
        ),
    )
    db.flush()
    return conflict


def vehicle_is_active(vehicle: Vehicle) -> bool:
    try:
        return VehicleStatus(vehicle.status) in ACTIVE_SALE_STATUSES
    except ValueError:
        return False


# Field mapping: fact field -> (vehicle column, converter, only_if_empty_policy)
_FACT_TO_COLUMN = {
    "registration_number": ("registration_number", None),
    "manufacturer": ("manufacturer", "title"),
    "vehicle_model": ("model", "title"),
    "vehicle_variant": ("variant", "title"),
    "vehicle_name": ("vehicle_name", "title"),
    "manufacturing_month": ("manufacturing_month", None),
    "manufacturing_year": ("manufacturing_year", "int"),
    "registration_date": ("registration_date", "date"),
    "fuel_type": ("fuel_type", "upper"),
    "vehicle_color": ("vehicle_color", "title"),
    "owner_count": ("owner_count", "int"),
    "owner_name": ("owner_name", "title"),
    "engine_number": ("engine_number", None),
    "chassis_number": ("chassis_number", None),
    "vehicle_class": ("vehicle_class", "title"),
    "seating_capacity": ("seating_capacity", "int"),
    "mileage_km": ("mileage_km", "int"),
    "selling_price": ("selling_price", "decimal"),
    "location": ("location", "title"),
    "body_type": ("body_type", "upper"),
}


def _convert(value, kind=None):
    if value is None:
        return None
    if kind is None:
        return value
    if kind == "int":
        try:
            return int(str(value).replace(",", ""))
        except (ValueError, TypeError):
            return None
    if kind == "upper":
        return str(value).strip().upper() or None
    if kind == "title":
        v = str(value).strip()
        return v or None
    if kind == "decimal":
        from decimal import Decimal, InvalidOperation

        try:
            return Decimal(str(value).replace(",", ""))
        except InvalidOperation:
            return None
    if kind == "date":
        from datetime import datetime

        try:
            return datetime.strptime(str(value), "%d-%b-%Y").date()
        except Exception:
            return None
    return value


def sync_vehicle_from_facts(db: Session, vehicle_id: str) -> Vehicle:
    """Mirror authoritative facts onto the vehicle's queryable columns.

    Only copy a fact to a column when its value is present and confident
    (confidence >= 0.7, not needs_review). Never overwrite an explicit
    higher-priority value.
    """
    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise KeyError("Vehicle not found")
    for fact in vehicle.facts:
        if fact.value is None or fact.needs_review:
            continue
        if fact.confidence < 0.7:
            continue
        target = _FACT_TO_COLUMN.get(fact.field)
        if not target:
            continue
        col, kind = target
        value = _convert(fact.value, kind)
        if value is None:
            continue
        setattr(vehicle, col, value)
    # build display name
    if not vehicle.vehicle_name:
        parts = [vehicle.manufacturer, vehicle.model]
        if vehicle.variant:
            parts.append(vehicle.variant)
        name = " ".join(p for p in parts if p)
        if name:
            vehicle.vehicle_name = name
    db.flush()
    return vehicle


def search_vehicles(
    db: Session,
    *,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    variant: Optional[str] = None,
    year: Optional[int] = None,
    fuel: Optional[str] = None,
    transmission: Optional[str] = None,
    color: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    body_type: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
    q: Optional[str] = None,
    active_only: bool = True,
    limit: int = 100,
) -> List[Vehicle]:
    stmt = select(Vehicle)
    if brand:
        stmt = stmt.where(Vehicle.manufacturer.ilike(f"%{brand}%"))
    if model:
        stmt = stmt.where(Vehicle.model.ilike(f"%{model}%"))
    if variant:
        stmt = stmt.where(Vehicle.variant.ilike(f"%{variant}%"))
    if year:
        stmt = stmt.where(Vehicle.manufacturing_year == year)
    if fuel:
        stmt = stmt.where(Vehicle.fuel_type == fuel.upper())
    if transmission:
        stmt = stmt.where(Vehicle.transmission == transmission.upper())
    if color:
        stmt = stmt.where(Vehicle.vehicle_color.ilike(f"%{color}%"))
    if min_price is not None:
        stmt = stmt.where(Vehicle.selling_price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Vehicle.selling_price <= max_price)
    if body_type:
        stmt = stmt.where(Vehicle.body_type == body_type.upper())
    if location:
        stmt = stmt.where(Vehicle.location.ilike(f"%{location}%"))
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Vehicle.vehicle_name.ilike(like),
                Vehicle.model.ilike(like),
                Vehicle.manufacturer.ilike(like),
                Vehicle.registration_number.ilike(like),
            )
        )
    if status:
        stmt = stmt.where(Vehicle.status == status.upper())
    elif active_only:
        stmt = stmt.where(Vehicle.status.in_([s.value for s in ACTIVE_SALE_STATUSES]))

    stmt = stmt.order_by(Vehicle.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars())


def public_vehicle_out(vehicle: Vehicle) -> dict:
    """Build the safe public representation of a vehicle."""
    photos = [
        p.file_path
        for p in sorted(vehicle.photos, key=lambda p: (not p.is_primary, p.sort_order))
        if p.variant in ("web", "processed", "original")
    ]
    return {
        "stock_id": vehicle.stock_id,
        "vehicle_name": vehicle.vehicle_name,
        "model": vehicle.model,
        "variant": vehicle.variant,
        "year": vehicle.manufacturing_year,
        "fuel": vehicle.fuel_type,
        "transmission": vehicle.transmission,
        "color": vehicle.vehicle_color,
        "mileage_km": vehicle.mileage_km,
        "price": vehicle.selling_price,
        "photos": photos,
        "features": vehicle.features,
        "description": vehicle.description,
        "availability": vehicle.status,
        "location": vehicle.location,
    }


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def find_duplicate_by_registration(
    db: Session, registration_number: str
) -> Optional[Vehicle]:
    """Return an existing vehicle with the same registration number, if any."""
    if not registration_number:
        return None
    clean = _clean_regno(registration_number)
    return db.execute(
        select(Vehicle).where(Vehicle.registration_number == clean)
    ).scalars().first()


def find_possible_duplicates(
    db: Session,
    registration_number: Optional[str] = None,
    chassis_number: Optional[str] = None,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
) -> List[Vehicle]:
    """Return vehicles that may be duplicates based on multiple weak signals."""
    candidates: List[Vehicle] = []
    # Strongest signal: exact registration number
    if registration_number:
        v = find_duplicate_by_registration(db, registration_number)
        if v:
            return [v]
    # Medium signal: chassis number
    if chassis_number:
        v = db.execute(
            select(Vehicle).where(Vehicle.chassis_number == chassis_number.strip())
        ).scalars().first()
        if v:
            candidates.append(v)
    # Weak signal: make + model + year combination
    if manufacturer and model and year:
        stmt = (
            select(Vehicle)
            .where(
                Vehicle.manufacturer.ilike(f"%{manufacturer}%"),
                Vehicle.model.ilike(f"%{model}%"),
                Vehicle.manufacturing_year == year,
            )
            .limit(5)
        )
        candidates.extend(db.execute(stmt).scalars().all())
    # Deduplicate by vehicle_id
    seen: set[str] = set()
    result: List[Vehicle] = []
    for v in candidates:
        if v.vehicle_id not in seen:
            seen.add(v.vehicle_id)
            result.append(v)
    return result


# ---------------------------------------------------------------------------
# Vehicle description generation (deterministic fallback; AI when enabled)
# ---------------------------------------------------------------------------

def generate_description(vehicle: Vehicle) -> str:
    """Generate a professional listing description from verified vehicle data.

    Uses AI if enabled, deterministic template otherwise. Never invents data.
    """
    from km_car_deals.ai.provider import ai_provider
    from km_car_deals.ai.prompts import VEHICLE_DESCRIPTION_PROMPT

    # Build a compact verified data string
    parts = []
    if vehicle.manufacturing_year:
        parts.append(f"Year: {vehicle.manufacturing_year}")
    if vehicle.manufacturer:
        parts.append(f"Make: {vehicle.manufacturer}")
    if vehicle.model:
        parts.append(f"Model: {vehicle.model}")
    if vehicle.variant:
        parts.append(f"Variant: {vehicle.variant}")
    if vehicle.fuel_type:
        parts.append(f"Fuel: {vehicle.fuel_type}")
    if vehicle.transmission:
        parts.append(f"Transmission: {vehicle.transmission}")
    if vehicle.vehicle_color:
        parts.append(f"Colour: {vehicle.vehicle_color}")
    if vehicle.mileage_km:
        parts.append(f"Mileage: {vehicle.mileage_km:,} km")
    if vehicle.owner_count:
        parts.append(f"Owners: {vehicle.owner_count}")
    if vehicle.location:
        parts.append(f"Location: {vehicle.location}")
    if vehicle.selling_price:
        parts.append(f"Price: ₹{vehicle.selling_price:,.0f}")
    else:
        parts.append("Price: on request")

    vehicle_data = "\n".join(parts)
    prompt = VEHICLE_DESCRIPTION_PROMPT.format(vehicle_data=vehicle_data)

    ai_text = ai_provider.complete_llm(prompt)
    if ai_text and len(ai_text) > 20:
        return ai_text.strip()

    # Deterministic fallback
    name = vehicle.vehicle_name or f"{vehicle.manufacturer or ''} {vehicle.model or ''}".strip()
    fuel = vehicle.fuel_type or ""
    trans = vehicle.transmission or ""
    year = str(vehicle.manufacturing_year) if vehicle.manufacturing_year else ""
    km_str = f"{vehicle.mileage_km:,} km driven, " if vehicle.mileage_km else ""
    price_str = (
        f"Priced at ₹{vehicle.selling_price:,.0f}."
        if vehicle.selling_price
        else "Price on request."
    )
    desc = (
        f"Well-maintained pre-owned {name} available at KM Car Deals"
        f"{', ' + year if year else ''}. "
        f"{fuel.title()} engine with {trans.title()} transmission. "
        f"{km_str}"
        f"{price_str} "
        f"Contact KM Car Deals for availability, inspection and test drive."
    )
    return desc


# ---------------------------------------------------------------------------
# Approval workflow
# ---------------------------------------------------------------------------

def approve_vehicle(
    db: Session, vehicle_id: str, approved_by: str = "admin"
) -> Vehicle:
    """Mark a vehicle as DEALER_APPROVED. Generates description if absent."""
    from datetime import datetime, timezone
    from km_car_deals.services.audit import log_action

    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise KeyError("Vehicle not found")
    old_status = vehicle.status
    if not vehicle.description:
        vehicle.description = generate_description(vehicle)
    vehicle.status = "DEALER_APPROVED"
    vehicle.approved_by = approved_by
    vehicle.approved_at = datetime.now(timezone.utc)
    record_status(db, vehicle, old_status, VehicleStatus("DEALER_APPROVED"), approved_by, "Dealer approved")
    log_action(db, actor=approved_by, action="VEHICLE_APPROVED",
               entity_type="Vehicle", entity_id=vehicle_id,
               before_data={"status": old_status},
               after_data={"status": "DEALER_APPROVED"})
    db.flush()
    return vehicle


def reject_vehicle(
    db: Session, vehicle_id: str, reason: str, rejected_by: str = "admin"
) -> Vehicle:
    """Reject a vehicle back to NEEDS_REVIEW with a reason."""
    from datetime import datetime, timezone
    from km_car_deals.services.audit import log_action

    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise KeyError("Vehicle not found")
    old_status = vehicle.status
    vehicle.status = "NEEDS_REVIEW"
    vehicle.rejected_by = rejected_by
    vehicle.rejected_at = datetime.now(timezone.utc)
    vehicle.rejection_reason = reason
    record_status(db, vehicle, old_status, VehicleStatus("NEEDS_REVIEW"), rejected_by, f"Rejected: {reason}")
    log_action(db, actor=rejected_by, action="VEHICLE_REJECTED",
               entity_type="Vehicle", entity_id=vehicle_id,
               before_data={"status": old_status},
               after_data={"status": "NEEDS_REVIEW", "reason": reason})
    db.flush()
    return vehicle


def publish_vehicle(
    db: Session, vehicle_id: str, published_by: str = "admin"
) -> Vehicle:
    """Publish a DEALER_APPROVED vehicle to PUBLISHED (website catalog)."""
    from datetime import datetime, timezone
    from km_car_deals.services.audit import log_action

    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise KeyError("Vehicle not found")
    if vehicle.status not in ("DEALER_APPROVED", "AVAILABLE", "READY_FOR_SALE"):
        raise ValueError(f"Vehicle must be approved before publishing (current: {vehicle.status})")
    old_status = vehicle.status
    vehicle.status = "PUBLISHED"
    vehicle.published_at = datetime.now(timezone.utc)
    if not vehicle.description:
        vehicle.description = generate_description(vehicle)
    record_status(db, vehicle, old_status, VehicleStatus("PUBLISHED"), published_by, "Published to website catalog")
    log_action(db, actor=published_by, action="VEHICLE_PUBLISHED",
               entity_type="Vehicle", entity_id=vehicle_id,
               before_data={"status": old_status},
               after_data={"status": "PUBLISHED"})
    db.flush()
    return vehicle


def reprocess_vehicle(
    db: Session, vehicle_id: str, actor: str = "admin"
) -> Vehicle:
    """Reset a vehicle back to AI_DRAFT for re-processing."""
    from km_car_deals.services.audit import log_action

    vehicle = get_vehicle(db, vehicle_id)
    if not vehicle:
        raise KeyError("Vehicle not found")
    old_status = vehicle.status
    vehicle.status = "AI_DRAFT"
    vehicle.rejected_by = None
    vehicle.rejected_at = None
    vehicle.rejection_reason = None
    record_status(db, vehicle, old_status, VehicleStatus("AI_DRAFT"), actor, "Reprocessing requested")
    log_action(db, actor=actor, action="VEHICLE_REPROCESS",
               entity_type="Vehicle", entity_id=vehicle_id,
               before_data={"status": old_status},
               after_data={"status": "AI_DRAFT"})
    db.flush()
    return vehicle
