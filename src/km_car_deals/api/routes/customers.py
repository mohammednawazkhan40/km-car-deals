"""Customer CRM API routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from km_car_deals.db.session import get_db
from km_car_deals.models.customer import (
    Customer,
    CustomerFollowup,
    CustomerMessage,
    HumanHandoffTask,
)
from km_car_deals.models.enums import FollowupStatus, HumanHandoffStatus
from km_car_deals.schemas.customer import (
    CustomerFollowupCreate,
    CustomerOut,
    FollowupOut,
    HandoffOut,
)
from km_car_deals.services import crm

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=List[CustomerOut])
def list_customers(
    lead_status: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    stmt = select(Customer)
    if lead_status:
        stmt = stmt.where(Customer.lead_status == lead_status.upper())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Customer.name.ilike(like) | Customer.whatsapp_number.ilike(like))
    stmt = stmt.order_by(Customer.created_at.desc())
    return list(db.execute(stmt).scalars())


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    c = db.get(Customer, customer_id)
    if not c:
        raise HTTPException(404, "Customer not found")
    return c


@router.get("/{customer_id}/messages")
def customer_messages(customer_id: str, db: Session = Depends(get_db)):
    return list(
        db.execute(
            select(CustomerMessage)
            .where(CustomerMessage.customer_id == customer_id)
            .order_by(CustomerMessage.created_at.desc())
            .limit(50)
        ).scalars()
    )


@router.get("/{customer_id}/followups", response_model=List[FollowupOut])
def customer_followups(customer_id: str, db: Session = Depends(get_db)):
    return list(
        db.execute(
            select(CustomerFollowup)
            .where(CustomerFollowup.customer_id == customer_id)
            .order_by(CustomerFollowup.created_at)
        ).scalars()
    )


@router.post("/{customer_id}/followups", response_model=FollowupOut)
def create_followup(customer_id: str, payload: CustomerFollowupCreate, db: Session = Depends(get_db)):
    f = crm.create_followup(
        db,
        customer_id=customer_id,
        scheduled_for=payload.scheduled_for,
        reason=payload.reason,
        vehicle_id=payload.vehicle_id,
        preferred_channel=payload.preferred_channel,
        message_template=payload.message_template,
        created_by="api",
    )
    db.commit()
    return f


@router.post("/{customer_id}/opt-out")
def mark_opt_out(customer_id: str, db: Session = Depends(get_db)):
    crm.mark_opt_out(db, customer_id, reason="admin_request")
    db.commit()
    return {"status": "opted_out"}


@router.post("/{customer_id}/opt-in")
def mark_opt_in(customer_id: str, db: Session = Depends(get_db)):
    crm.mark_opt_in(db, customer_id)
    db.commit()
    return {"status": "opted_in"}


@router.get("/{customer_id}/handoffs", response_model=List[HandoffOut])
def customer_handoffs(customer_id: str, db: Session = Depends(get_db)):
    return list(
        db.execute(
            select(HumanHandoffTask).where(HumanHandoffTask.customer_id == customer_id)
        ).scalars()
    )


@router.post("/{customer_id}/followup-message")
def generate_followup_message(customer_id: str, db: Session = Depends(get_db)):
    """Generate an AI follow-up WhatsApp message for a customer."""
    from km_car_deals.ai.provider import ai_provider
    from km_car_deals.ai.prompts import FOLLOWUP_MESSAGE_PROMPT
    from km_car_deals.services import inventory as inv_svc

    c = db.get(Customer, customer_id)
    if not c:
        raise HTTPException(404, "Customer not found")

    # Find their most recent interest vehicle
    vehicle_name = c.preferred_vehicle or "a vehicle"
    vehicle_status = "unknown"
    if c.interests:
        latest = sorted(c.interests, key=lambda x: x.created_at, reverse=True)[0]
        v = inv_svc.get_vehicle(db, latest.vehicle_id)
        if v:
            vehicle_name = v.vehicle_name or vehicle_name
            vehicle_status = v.status

    last_contact = "recently"
    if c.last_outbound_at:
        last_contact = c.last_outbound_at.strftime("%d %b %Y")

    prompt = FOLLOWUP_MESSAGE_PROMPT.format(
        customer_name=c.name or "Customer",
        vehicle_interest=vehicle_name,
        lead_status=c.lead_status,
        vehicle_availability=vehicle_status,
        last_contact=last_contact,
        notes=c.notes or "",
    )
    ai_msg = ai_provider.complete_llm(prompt)
    if not ai_msg or len(ai_msg) < 10:
        # deterministic fallback
        ai_msg = (
            f"Hello {c.name or 'there'}, this is KM Car Deals following up on your interest "
            f"in {vehicle_name}. Please let us know if you'd like to schedule a visit or test drive. "
            f"- KM Car Deals"
        )
    return {"customer_id": customer_id, "message": ai_msg.strip()}


@router.patch("/{customer_id}/lead-status")
def update_lead_status(
    customer_id: str,
    status: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Update a customer's lead pipeline status."""
    c = db.get(Customer, customer_id)
    if not c:
        raise HTTPException(404, "Customer not found")
    old = c.lead_status
    c.lead_status = status.upper()
    if notes:
        c.notes = notes
    crm.add_interaction(db, customer_id, "NOTE", summary=f"Lead status changed: {old} → {c.lead_status}")
    db.commit()
    return {"customer_id": customer_id, "lead_status": c.lead_status}
