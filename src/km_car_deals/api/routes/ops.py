"""Operations routes: follow-up processing, catalog, instagram, excel, analytics."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from km_car_deals.agents.followup_agent import CustomerFollowupAgent
from km_car_deals.db.session import get_db
from km_car_deals.models.customer import Customer, HumanHandoffTask
from km_car_deals.models.vehicle import Vehicle, VehicleStatusHistory
from km_car_deals.services import catalog as catalog_service
from km_car_deals.services.excel_service import ExcelService

router = APIRouter(prefix="/ops", tags=["operations"])


# ---------------- Follow-ups ----------------
@router.get("/followups/due")
def list_due_followups(db: Session = Depends(get_db)):
    agent = CustomerFollowupAgent(db)
    return [f.followup_id for f in agent.due_followups()]


@router.post("/followups/process")
async def process_due_followups(
    auto_send: bool = False, db: Session = Depends(get_db)
):
    agent = CustomerFollowupAgent(db)
    results = await agent.process_due(auto_send=auto_send)
    db.commit()
    return {"processed": len(results), "results": results}


@router.post("/followups/mark-overdue")
def mark_overdue(db: Session = Depends(get_db)):
    agent = CustomerFollowupAgent(db)
    n = agent.mark_overdue()
    db.commit()
    return {"marked_overdue": n}


# ---------------- Catalog ----------------
@router.post("/catalog/sync")
def sync_catalog(db: Session = Depends(get_db)):
    manager = catalog_service.WhatsAppCatalogManager(db)
    stats = manager.sync_all_entries()
    db.commit()
    return stats


@router.get("/catalog")
def list_catalog(db: Session = Depends(get_db)):
    from km_car_deals.models.catalog import WhatsAppCatalogEntry

    return list(db.execute(select(WhatsAppCatalogEntry)).scalars())


@router.post("/catalog/push/{entry_id}")
async def push_catalog_entry(entry_id: str, db: Session = Depends(get_db)):
    from km_car_deals.models.catalog import WhatsAppCatalogEntry

    entry = db.get(WhatsAppCatalogEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Catalog entry not found")
    manager = catalog_service.WhatsAppCatalogManager(db)
    result = await manager.push_to_meta(entry)
    db.commit()
    return result


# ---------------- Instagram ----------------
@router.post("/instagram/generate/{vehicle_id}")
def generate_instagram(vehicle_id: str, db: Session = Depends(get_db)):
    from km_car_deals.agents.instagram_agent import InstagramMarketingAgent

    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(404, "Vehicle not found")
    agent = InstagramMarketingAgent(db)
    content = agent.generate_draft(vehicle)
    db.commit()
    return {"content_id": content.content_id, "status": content.status, "caption": content.caption}


@router.post("/instagram/approve/{content_id}")
def approve_instagram(
    content_id: str, approved_by: str = "admin", db: Session = Depends(get_db)
):
    from km_car_deals.agents.instagram_agent import InstagramMarketingAgent

    agent = InstagramMarketingAgent(db)
    content = agent.approve(content_id, approved_by)
    if not content:
        raise HTTPException(404, "Content not found")
    db.commit()
    return {"content_id": content_id, "status": content.status}


@router.post("/instagram/publish/{content_id}")
async def publish_instagram(content_id: str, db: Session = Depends(get_db)):
    from km_car_deals.agents.instagram_agent import InstagramMarketingAgent
    from km_car_deals.models.catalog import SocialContent

    content = db.get(SocialContent, content_id)
    if not content:
        raise HTTPException(404, "Content not found")
    agent = InstagramMarketingAgent(db)
    result = await agent.publish(content)
    db.commit()
    return result


# ---------------- Excel ----------------
@router.post("/excel/export")
def export_excel(db: Session = Depends(get_db)):
    service = ExcelService(db)
    path = service.export_inventory()
    return {"path": path}


@router.post("/excel/crm-import")
def import_crm_excel(
    file: UploadFile = File(...),
    confirm_duplicates: bool = False,
    db: Session = Depends(get_db),
):
    import tempfile, os

    data = file.file.read()
    ext = os.path.splitext(file.filename or "")[1] or ".xlsx"
    fd, tmp = tempfile.mkstemp(suffix=ext)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    try:
        service = ExcelService(db)
        result = service.import_crm_excel(tmp, confirm_duplicates=confirm_duplicates)
        db.commit()
        return result
    finally:
        os.remove(tmp)


# ---------------- Analytics ----------------
@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    total_vehicles = db.execute(select(func.count(Vehicle.vehicle_id))).scalar()
    active = db.execute(
        select(func.count(Vehicle.vehicle_id)).where(
            Vehicle.status.in_(["AVAILABLE", "READY_FOR_SALE", "NEGOTIATION", "RESERVED"])
        )
    ).scalar()
    sold = db.execute(
        select(func.count(Vehicle.vehicle_id)).where(Vehicle.status == "SOLD")
    ).scalar()
    total_customers = db.execute(select(func.count(Customer.customer_id))).scalar()
    open_handoffs = db.execute(
        select(func.count(HumanHandoffTask.task_id)).where(HumanHandoffTask.status == "OPEN")
    ).scalar()
    status_breakdown = {
        r[0]: r[1]
        for r in db.execute(
            select(Vehicle.status, func.count(Vehicle.vehicle_id))
            .group_by(Vehicle.status)
        ).all()
    }
    return {
        "total_vehicles": total_vehicles,
        "active_for_sale": active,
        "sold": sold,
        "total_customers": total_customers,
        "open_handoffs": open_handoffs,
        "status_breakdown": status_breakdown,
    }
