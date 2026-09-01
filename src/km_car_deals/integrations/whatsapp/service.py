"""WhatsApp message service: logging, consent updates, and policy-gated sending."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from km_car_deals.core.config import settings
from km_car_deals.core.logging import get_logger
from km_car_deals.integrations.whatsapp.client import wa_client
from km_car_deals.integrations.whatsapp.policy import WhatsAppPolicy
from km_car_deals.models.customer import Customer, CustomerMessage
from km_car_deals.services import crm

logger = get_logger(__name__)

STOP_WORDS = ("stop", "unsubscribe", "opt out", "don't contact", "do not contact", "banned")
OPT_IN_WORDS = ("subscribe", "yes i want updates", "opt in", "i agree to receive")


def log_message(
    db: Session,
    customer_id: str,
    direction: str,
    content: Optional[str] = None,
    channel: str = "WHATSAPP",
    meta_message_id: Optional[str] = None,
    media_type: Optional[str] = None,
    template_used: Optional[str] = None,
) -> CustomerMessage:
    customer = db.get(Customer, customer_id)
    now = datetime.now(timezone.utc)
    msg = CustomerMessage(
        message_id=meta_message_id or str(uuid.uuid4()),
        customer_id=customer_id,
        direction=direction,
        channel=channel,
        content=content,
        media_type=media_type,
        meta_message_id=meta_message_id,
        template_used=template_used,
        sent_at=now,
    )
    if direction == "INBOUND":
        if customer:
            customer.last_inbound_at = now
            customer.conversation_window_open = True
    else:
        if customer:
            customer.last_outbound_at = now
    # Handle opt-out / consent on inbound text
    if direction == "INBOUND" and content:
        lowered = content.strip().lower()
        if any(w in lowered for w in STOP_WORDS):
            crm.mark_opt_out(db, customer_id, reason="user_request_stop", source_message=content)
        elif any(w in lowered for w in OPT_IN_WORDS):
            crm.mark_opt_in(db, customer_id, source_message=content)
    db.add(msg)
    db.flush()
    return msg


async def send_text_message(
    db: Session,
    customer: Customer,
    body: str,
    *,
    is_marketing: bool = True,
) -> dict:
    """Send a text message subject to policy. Logs it regardless."""
    policy = WhatsAppPolicy(db)
    decision = policy.check(customer, is_marketing=is_marketing)
    logger.info("Message policy for %s: %s (%s)", customer.customer_id, decision.allowed, decision.reason)

    to = customer.whatsapp_number or customer.phone_number
    if not to:
        raise ValueError("Customer has no WhatsApp/phone number")

    # Always log the message we attempted or would send.
    log_message(db, customer.customer_id, "OUTBOUND", content=body)

    if not settings.SEND_MESSAGES_AUTOMATICALLY:
        return {
            "sent": False,
            "reason": "automatic_sending_disabled; message queued/paused",
            "policy": decision.reason,
        }

    if not decision.allowed and not decision.should_use_template:
        return {"sent": False, "reason": f"policy_blocked:{decision.reason}"}

    if decision.allowed:
        resp = await wa_client.send_text(to, body)
        _mark_send_success(db, customer, resp)
        return {"sent": True, "response": resp}

    # Permission to send but needs template -> use configured template
    if settings.WHATSAPP_TEMPLATE:
        resp = await wa_client.send_template(to, settings.WHATSAPP_TEMPLATE)
        return {"sent": True, "via_template": True, "response": resp}
    return {"sent": False, "reason": "template_required_and_unconfigured"}


def list_recent_messages(db: Session, customer_id: str, limit: int = 50) -> List[CustomerMessage]:
    return list(
        db.execute(
            select(CustomerMessage)
            .where(CustomerMessage.customer_id == customer_id)
            .order_by(CustomerMessage.created_at.desc())
            .limit(limit)
        ).scalars()
    )
