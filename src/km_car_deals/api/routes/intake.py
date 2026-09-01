"""Vehicle intake API routes - accepts multi-file + text intake."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from km_car_deals.agents.intake_agent import CarIntakeAgent
from km_car_deals.db.session import get_db
from km_car_deals.image_processing.processor import available_backgrounds
from km_car_deals.schemas.vehicle import IntakeResult

router = APIRouter(prefix="/intake", tags=["intake"])


@router.post("/vehicle", response_model=IntakeResult)
async def intake_vehicle(
    files: List[UploadFile] = File(default=[]),
    message: str = Form(""),
    seller_whatsapp: Optional[str] = Form(None),
    process_images: bool = Form(False),
    background: str = Form("premium_showroom"),
    db: Session = Depends(get_db),
):
    """Receive 1-10 photos, RC image/PDF, other docs, and a text message.

    Runs the CarIntakeAgent pipeline and returns the created vehicle + notices.
    """
    if len(files) > 15:
        raise HTTPException(400, "Too many files. Max 15 allowed.")

    file_items = []
    for f in files:
        data = await f.read()
        if len(data) == 0:
            continue
        file_items.append((data, f.filename or "file"))

    agent = CarIntakeAgent(db)
    try:
        vehicle, notices = agent.run_intake(
            file_items, message=message, seller_whatsapp=seller_whatsapp
        )
    finally:
        pass

    if process_images and vehicle.photos:
        from km_car_deals.agents.image_agent import VehicleImageAgent

        VehicleImageAgent(db).process_vehicle_photos(
            vehicle.vehicle_id, vehicle.photos, background=background
        )

    db.commit()
    return IntakeResult(
        status=vehicle.status,
        vehicle_id=vehicle.vehicle_id,
        message="; ".join(notices) or "Vehicle intake completed.",
        conflicts_created=len(vehicle.conflicts),
    )


@router.get("/backgrounds")
def backgrounds():
    return available_backgrounds()
