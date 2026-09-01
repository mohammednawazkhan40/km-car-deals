"""Phase 1 tests: vehicle inventory, facts, status, conflicts, search, availability."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from km_car_deals.models.enums import ConflictStatus, SourceType, VehicleStatus
from km_car_deals.models.vehicle import Vehicle, VehicleConflict, VehicleStatusHistory
from km_car_deals.schemas.vehicle import VehicleCreate, VehicleFactIn
from km_car_deals.services import inventory


def _vc(**kw) -> VehicleCreate:
    defaults = dict(
        manufacturer="Hyundai",
        model="Creta",
        variant="SX",
        manufacturing_year=2022,
        fuel_type="DIESEL",
        selling_price=Decimal("1250000"),
        mileage_km=22000,
        location="Mumbai",
    )
    defaults.update(kw)
    return VehicleCreate(**defaults)


def test_create_vehicle_and_stock_id(db):
    a = inventory.create_vehicle(db, _vc())
    b = inventory.create_vehicle(db, _vc())
    assert a.stock_id and a.stock_id != b.stock_id
    assert a.status == VehicleStatus.NEW.value
    # status history recorded
    hist = db.execute(select(VehicleStatusHistory)).scalars().all()
    assert any(h.vehicle_id == a.vehicle_id for h in hist)


def test_fact_set_and_sync(db):
    v = inventory.create_vehicle(db, _vc())
    inventory.set_fact(
        db,
        v.vehicle_id,
        VehicleFactIn(field="owner_count", value="2", source=SourceType.RC.value, confidence=0.9),
    )
    inventory.sync_vehicle_from_facts(db, v.vehicle_id)
    db.refresh(v)
    assert v.owner_count == 2
    # vehicle_name built from manufacturer + model
    assert v.vehicle_name and "Creta" in v.vehicle_name


def test_low_confidence_fact_not_synced(db):
    v = inventory.create_vehicle(db, _vc())
    inventory.set_fact(
        db,
        v.vehicle_id,
        VehicleFactIn(field="fuel_type", value="PETROL", source="ai", confidence=0.4),
    )
    inventory.sync_vehicle_from_facts(db, v.vehicle_id)
    db.refresh(v)
    assert v.fuel_type == "DIESEL"  # explicit create value not overridden


def test_status_transition_records_history(db):
    v = inventory.create_vehicle(db, _vc())
    inventory.update_status(db, v.vehicle_id, VehicleStatus.AVAILABLE.value, reason="ready")
    db.refresh(v)
    assert v.status == VehicleStatus.AVAILABLE.value
    hist = db.execute(select(VehicleStatusHistory)).scalars().all()
    recent = [h for h in hist if h.vehicle_id == v.vehicle_id]
    assert any(h.to_status == VehicleStatus.AVAILABLE.value for h in recent)


def test_active_status_availability(db):
    v = inventory.create_vehicle(db, _vc())
    assert inventory.vehicle_is_active(v) is False  # NEW is not active-sale
    inventory.update_status(db, v.vehicle_id, VehicleStatus.AVAILABLE.value)
    db.refresh(v)
    assert inventory.vehicle_is_active(v) is True


def test_conflict_create_and_resolve(db):
    v = inventory.create_vehicle(db, _vc())
    conflict = inventory.create_conflict(
        db, v.vehicle_id, "manufacturing_year",
        SourceType.RC.value, "2021", "user", "2022", "year mismatch",
    )
    assert conflict.status == ConflictStatus.OPEN.value
    assert len(inventory.open_conflicts(db, v.vehicle_id)) == 1
    inventory.resolve_conflict(db, v.vehicle_id, conflict.conflict_id, "2022", "admin")
    assert inventory.open_conflicts(db, v.vehicle_id) == []


def test_search_vehicles_filters(db):
    inventory.create_vehicle(db, _vc())
    gas = _vc(manufacturer="Tata", model="Nexon", fuel_type="PETROL", selling_price=Decimal("900000"))
    gas_vehicle = inventory.create_vehicle(db, gas)
    inventory.update_status(db, gas_vehicle.vehicle_id, VehicleStatus.AVAILABLE.value)
    db.flush()
    # active_only excludes NEW vehicles by default
    assert inventory.search_vehicles(db, brand="Hyundai") == []
    assert len(inventory.search_vehicles(db, brand="Tata")) == 1
    res = inventory.search_vehicles(db, brand="Tata", fuel="petrol")
    assert res and res[0].model == "Nexon"
    res = inventory.search_vehicles(db, max_price=1000000)
    assert all(v.selling_price <= 1000000 for v in res)


def test_public_vehicle_out_is_safe(db):
    v = inventory.create_vehicle(db, _vc(registration_number="MH01 AB 1234"))
    v.owner_name = "Secret Owner"
    db.flush()
    public = inventory.public_vehicle_out(v)
    assert "owner_name" not in public
    assert "registration_number" not in public
    assert "Secret" not in str(public)
    assert "MH01" not in str(public)
    assert public["availability"] == v.status