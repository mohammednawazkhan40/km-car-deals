"""Customer CRM service: customer records, dedupe, leads, interests, interactions."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from km_car_deals.core.logging import get_logger
from km_car_deals.models.customer import (
    Customer,
    CustomerConsent,
    CustomerFollowup,
    CustomerInteraction,
    CustomerVehicleInterest,
    HumanHandoffTask,
)
from km_car_deals.models.enums import (
    ConsentStatus,
    FollowupStatus,
    HumanHandoffStatus,
    InteractionType,
    LeadStatus,
)

logger = get_logger(__name__)


def normalize_phone(raw: str) -> str:
    """Normalize an Indian/mobile phone number to E.164-ish form."""
    if not raw:
        return ""
    digits = re.sub(r"[^\d]", "", raw)
    if len(digits) == 10:
        return "91" + digits
    if len(digits) == 12 and digits.startswith("91"):
        return digits
    if len(digits) == 11 and digits.startswith("0"):
        return "91" + digits[1:]
    return digits


def find_duplicate_customer(
    db: Session,
    phone: Optional[str] = None,
    whatsapp: Optional[str] = None,
    email: Optional[str] = None,
) -> Optional[Customer]:
    """Locate an existing customer matching phone/whatsapp/email."""
    if not any([phone, whatsapp, email]):
        return None
    clauses = []
    if phone:
        clauses.append(Customer.phone_number == phone)
    if whatsapp:
        clauses.append(Customer.whatsapp_number == whatsapp)
    if email and "@" in email:
        clauses.append(Customer.email == email)
    if not clauses:
        return None
    return db.execute(select(Customer).where(or_(*clauses))).scalars().first()


def get_or_create_customer(
    db: Session,
    *,
    whatsapp: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    name: Optional[str] = None,
    source: Optional[str] = None,
) -> tuple[Customer, bool]:
    """Return (customer, created). Dedupes on phone/whatsapp/email."""
    w = normalize_phone(whatsapp) if whatsapp else None
    p = normalize_phone(phone) if phone else None
    existing = find_duplicate_customer(db, phone=p, whatsapp=w, email=email)
    if existing:
        if name and not existing.name:
            existing.name = name.strip()
        if w and not existing.whatsapp_number:
            existing.whatsapp_number = w
        if p and not existing.phone_number:
            existing.phone_number = p
        db.flush()
        return existing, False
    customer = Customer(
        name=name.strip() if name else None,
        phone_number=p,
        whatsapp_number=w,
        email=email,
        source=source,
        lead_status=LeadStatus.NEW.value,
    )
    db.add(customer)
    db.flush()
    return customer, True


def upsert_customer(db: Session, data: dict) -> tuple[Customer, bool]:
    """Upsert a customer payload; returns (customer, created)."""
    whatsapp = data.get("whatsapp_number")
    phone = data.get("phone_number")
    email = data.get("email")
    customer, created = get_or_create_customer(
        db,
        whatsapp=whatsapp,
        phone=phone,
        email=email,
        name=data.get("name"),
        source=data.get("source"),
    )
    for key, val in data.items():
        if val is None or key in ("customer_id",):
            continue
        if not hasattr(customer, key):
            continue
        if key in ("name", "phone_number", "whatsapp_number", "email") and created:
            # already set
            continue
        setattr(customer, key, val)
    db.flush()
    return customer, created


def add_interaction(
    db: Session,
    customer_id: str,
    interaction_type: str,
    summary: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    interaction_metadata: Optional[dict] = None,
) -> CustomerInteraction:
    obj = CustomerInteraction(
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        interaction_type=interaction_type,
        summary=summary,
        interaction_metadata=interaction_metadata,
    )
    db.add(obj)
    db.flush()
    return obj


def customer_vehicle_interest(
    db: Session,
    customer_id: str,
    vehicle_id: str,
    interest_type: str = "ENQUIRED",
    interest_status: str = "ACTIVE",
    notes: Optional[str] = None,
) -> CustomerVehicleInterest:
    interest = _interest_helper(db, customer_id, vehicle_id, interest_status)
    interest.interest_type = interest_type
    interest.interest_date = round_datetime()
    interest.last_contacted = round_datetime()
    if notes:
        interest.notes = notes
    flush(db)
    return interest


def _interest_helper(
    db: Session,
    customer_id: str,
    vehicle_id: str,
    interest_status: str,
) -> CustomerVehicleInterest:
    existing = db.execute(
        select(CustomerVehicleInterest).where(
            CustomerVehicleInterest.customer_id == customer_id,
            CustomerVehicleInterest.vehicle_id == vehicle_id,
        )
    ).scalar_one_or_none()
    if existing:
        existing.interest_status = interest_status
        db.flush()
        return existing
    obj = CustomerVehicleInterest(
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        interest_status=interest_status,
    )
    db.add(obj)
    db.flush()
    return obj


def mark_opt_out(
    db: Session, customer_id: str, reason: Optional[str] = None,
    source_message: Optional[str] = None
) -> None:
    customer = db.get(Customer, customer_id)
    if not customer:
        return
    customer.opt_out = True
    customer.opt_in = False
    customer.consent_status = ConsentStatus.OPTED_OUT.value
    customer.opt_out_reason = reason
    db.add(
        CustomerConsent(
            customer_id=customer_id,
            purpose="MARKETING",
            status=ConsentStatus.OPTED_OUT.value,
            channel="WHATSAPP",
            source_message=source_message,
            recorded_at=round_datetime(),
        )
    )
    add_interaction(db, customer_id, InteractionType.NOTE.value, "Customer opted out of marketing contact.")
    db.flush()


def mark_opt_in(db: Session, customer_id: str, source_message: Optional[str] = None) -> None:
    customer = db.get(Customer, customer_id)
    if not customer:
        return
    customer.opt_in = True
    customer.opt_out = False
    customer.consent_status = ConsentStatus.OPTED_IN.value
    db.add(
        CustomerConsent(
            customer_id=customer_id,
            purpose="MARKETING",
            status=ConsentStatus.OPTED_IN.value,
            channel="WHATSAPP",
            source_message=source_message,
            recorded_at=round_datetime(),
        )
    )
    db.flush()


def create_followup(
    db: Session,
    customer_id: str,
    scheduled_for=None,
    reason: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    preferred_channel: str = "WHATSAPP",
    message_template: Optional[str] = None,
    created_by: Optional[str] = None,
) -> CustomerFollowup:
    obj = CustomerFollowup(
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        scheduled_for=scheduled_for,
        reason=reason,
        status=FollowupStatus.PENDING.value,
        preferred_channel=preferred_channel,
        message_template=message_template,
        created_by=created_by,
    )
    db.add(obj)
    db.flush()
    return obj


def create_handoff(
    db: Session,
    reason: str,
    summary: Optional[str],
    customer_id: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    channel: Optional[str] = None,
    assigned_to: Optional[str] = None,
) -> HumanHandoffTask:
    obj = HumanHandoffTask(
        customer_id=customer_id,
        vehicle_id=vehicle_id,
        reason=reason,
        summary=summary,
        status=HumanHandoffStatus.OPEN.value,
        assigned_to=assigned_to,
        channel=channel,
    )
    db.add(obj)
    db.flush()
    return obj


def round_datetime() -> datetime:
    return datetime.now(timezone.utc)


def flush(db: Session) -> None:
    db.flush()
