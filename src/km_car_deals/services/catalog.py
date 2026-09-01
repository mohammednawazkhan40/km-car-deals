"""WhatsApp Catalog management.

Synchronizes eligible AVAILABLE vehicles with the configured Meta/WhatsApp
catalog using official product APIs. Never advertises non-active vehicles.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from km_car_deals.core.config import settings
from km_car_deals.core.logging import get_logger
from km_car_deals.models.catalog import WhatsAppCatalogEntry
from km_car_deals.models.enums import (
    ACTIVE_SALE_STATUSES,
    CatalogEntryStatus,
    VehicleStatus,
)
from km_car_deals.models.vehicle import Vehicle
from km_car_deals.services import inventory

logger = get_logger(__name__)


def eligible_vehicles(db: Session) -> List[Vehicle]:
    """Vehicles that should be in the active catalog."""
    return inventory.search_vehicles(db, active_only=True, limit=500)


class WhatsAppCatalogManager:
    """Builds and syncs catalog entries from vehicles."""

    def __init__(self, db: Session):
        self.db = db

    def _primary_image(self, vehicle: Vehicle) -> Optional[str]:
        for p in sorted(vehicle.photos, key=lambda p: (not p.is_primary, p.sort_order)):
            if p.variant in ("web", "processed"):
                return p.file_path
        return None

    def build_entry(self, vehicle: Vehicle) -> WhatsAppCatalogEntry:
        entry = new_or_existing(self.db, vehicle.vehicle_id)
        entry.title = vehicle.vehicle_name or f"{vehicle.manufacturer} {vehicle.model}"
        entry.description = self._description(vehicle)
        entry.price = str(int(vehicle.selling_price)) if vehicle.selling_price else None
        entry.currency = "INR"
        entry.availability = "in stock" if inventory.vehicle_is_active(vehicle) else "out of stock"
        entry.category = vehicle.body_type or "Cars"
        entry.image_url = self._primary_image(vehicle)
        entry.vehicle_id = vehicle.vehicle_id
        status = (
            CatalogEntryStatus.PUBLISHED.value
            if inventory.vehicle_is_active(vehicle)
            else CatalogEntryStatus.OUT_OF_STOCK.value
        )
        if vehicle.status == VehicleStatus.SOLD.value:
            status = CatalogEntryStatus.REMOVED.value
        entry.status = status
        entry.sync_status = "PENDING"
        self.db.flush()
        return entry

    def _description(self, vehicle: Vehicle) -> str:
        parts = []
        if vehicle.manufacturing_year:
            parts.append(f"{vehicle.manufacturing_year}")
        if vehicle.fuel_type:
            parts.append(vehicle.fuel_type)
        if vehicle.transmission:
            parts.append(vehicle.transmission)
        if vehicle.mileage_km:
            parts.append(f"{vehicle.mileage_km:,} km")
        if vehicle.owner_count is not None:
            parts.append(f"{vehicle.owner_count} owner(s)")
        base = " ".join(parts)
        return f"{base} | KM Car Deals" if base else "KM Car Deals"

    def sync_all_entries(self, active_vehicles: Optional[List[Vehicle]] = None) -> dict:
        """Synchronize the local catalog table for all vehicles.

        Returns counts of entries created/updated/removed by status.
        """
        vehicles = active_vehicles or eligible_vehicles(self.db)
        # Mark non-active vehicles' entries appropriately
        all_entries = list(
            self.db.execute(
                select(WhatsAppCatalogEntry).where(
                    WhatsAppCatalogEntry.vehicle_id.in_([v.vehicle_id for v in vehicles])
                )
            ).scalars()
        )
        existing_by_vehicle = {e.vehicle_id: e for e in all_entries}
        stats = {"created": 0, "updated": 0, "removed": 0, "out_of_stock": 0}

        for v in vehicles:
            entry = self.build_entry(v)
            if entry.vehicle_id in existing_by_vehicle:
                stats["updated"] += 1
            else:
                stats["created"] += 1
            if entry.status == CatalogEntryStatus.REMOVED.value:
                stats["removed"] += 1
            elif entry.status == CatalogEntryStatus.OUT_OF_STOCK.value:
                stats["out_of_stock"] += 1
            self.db.add(entry)
        self.db.flush()
        # Catalog auto-update on vehicle status (for remote sync hooks it's
        # called separately; here we just persist the correct local entries).
        return stats

    async def push_to_meta(self, entry: WhatsAppCatalogEntry) -> dict:
        """Push/update a product in the Meta WhatsApp catalog (official API).

        Requires META_WA_BUSINESS_ID and META_WA_CATALOG_ID plus access token.
        """
        from km_car_deals.integrations.whatsapp.commerce import CommerceClient
        from km_car_deals.integrations.whatsapp.client import wa_client

        if not (settings.META_WA_BUSINESS_ID and settings.META_WA_CATALOG_ID):
            entry.sync_status = "SKIPPED_NO_COMMERCE_CONFIG"
            entry.last_meta_error = "Meta commerce IDs not configured"
            self.db.flush()
            return {"synced": False, "reason": "no_commerce_config"}

        commerce = CommerceClient(
            access_token=wa_client.access_token,
            business_id=settings.META_WA_BUSINESS_ID,
            catalog_id=settings.META_WA_CATALOG_ID,
        )
        try:
            if entry.meta_product_id:
                resp = await commerce.update_product(entry)
            else:
                resp = await commerce.create_product(entry)
                entry.meta_product_id = resp.get("id")
            entry.sync_status = "SYNCED"
            entry.status = CatalogEntryStatus.PUBLISHED.value
            entry.last_meta_error = None
            self.db.flush()
            return {"synced": True, "response": resp}
        except Exception as exc:
            entry.sync_status = "FAILED"
            entry.last_meta_error = str(exc)
            self.db.flush()
            return {"synced": False, "reason": str(exc)}


def new_or_existing(db: Session, vehicle_id: str) -> WhatsAppCatalogEntry:
    existing = db.execute(
        select(WhatsAppCatalogEntry).where(
            WhatsAppCatalogEntry.vehicle_id == vehicle_id
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    return WhatsAppCatalogEntry(vehicle_id=vehicle_id)


def handle_vehicle_status_change(db: Session, vehicle_id: str) -> None:
    """Auto-update catalog when a vehicle status changes."""
    manager = WhatsAppCatalogManager(db)
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        return
    manager.build_entry(vehicle)
    db.flush()
