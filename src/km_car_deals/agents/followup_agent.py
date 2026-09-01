"""Customer Follow-up Agent.

Tracks and processes follow-up tasks, applies conversation rules and messaging
policy before any automated contact. Never messages aggressively or without
permission.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from km_car_deals.core.config import settings
from km_car_deals.core.logging import get_logger
from km_car_deals.integrations.whatsapp import service as whatsapp_service
from km_car_deals.models.customer import Customer, CustomerFollowup
from km_car_deals.models.enums import FollowupReason, FollowupStatus
from km_car_deals.models.vehicle import Vehicle

logger = get_logger(__name__)

FOLLOWUP_TEMPLATES = {
    FollowupReason.NEW_LEAD.value: "Hi {name}, this is KM Car Deals. Thanks for reaching out. How can we help you find the right car?",
    FollowupReason.VEHICLE_INTEREST.value: "Hi {name}, this is KM Car Deals. Just following up regarding the {vehicle} you were interested in. Would you like to see the latest details or photos?",
    FollowupReason.PRICE_DISCUSSION.value: "Hi {name}, just checking if you'd like to discuss the price or arrange a visit for the {vehicle}.",
    FollowupReason.CUSTOMER_DECISION.value: "Hi {name}, following up on your interest in the {vehicle}. Would you like any more details?",
    FollowupReason.TEST_DRIVE.value: "Hi {name}, are you all set for your test drive of the {vehicle}?",
    FollowupReason.BOOKING.value: "Hi {name}, let's confirm your booking for the {vehicle}. Please reply to proceed.",
    FollowupReason.CALL_REQUEST.value: "Hi {name}, this is a reminder that we planned to talk today about the {vehicle}.",
}


class CustomerFollowupAgent:
    def __init__(self, db: Session):
        self.db = db

    def due_followups(self, now: Optional[datetime] = None) -> List[CustomerFollowup]:
        now = now or datetime.now(timezone.utc)
        return list(
            self.db.execute(
                select(CustomerFollowup).where(
                    CustomerFollowup.status == FollowupStatus.PENDING.value,
                    CustomerFollowup.scheduled_for <= now,
                )
            ).scalars()
        )

    def mark_overdue(self) -> int:
        now = datetime.now(timezone.utc)
        rows = list(
            self.db.execute(
                select(CustomerFollowup).where(
                    CustomerFollowup.status == FollowupStatus.PENDING.value,
                    CustomerFollowup.scheduled_for < now,
                )
            ).scalars()
        )
        for f in rows:
            f.status = FollowupStatus.OVERDUE.value
        self.db.flush()
        return len(rows)

    async def process_due(self, auto_send: Optional[bool] = None) -> List[dict]:
        """Process due follow-ups. Returns results for each."""
        results = []
        send = settings.SEND_MESSAGES_AUTOMATICALLY if auto_send is None else auto_send
        for followup in self.due_followups():
            results.append(await self.process_one(followup, auto_send=send))
        return results

    async def process_one(
        self, followup: CustomerFollowup, auto_send: Optional[bool] = None
    ) -> dict:
        customer = self.db.get(Customer, followup.customer_id)
        if not customer:
            followup.status = FollowupStatus.CANCELLED.value
            self.db.flush()
            return {"followup_id": followup.followup_id, "status": "cancelled_no_customer"}

        if not followup.preferred_channel or followup.preferred_channel == "WHATSAPP":
            decision = await self._send_whatsapp_followup(followup, customer, auto_send)

        followup.status = FollowupStatus.COMPLETED.value
        followup.last_contacted = datetime.now(timezone.utc)
        if followup.vehicle_id:
            from km_car_deals.models.customer import CustomerVehicleInterest

            interest = self.db.execute(
                select(CustomerVehicleInterest).where(
                    CustomerVehicleInterest.customer_id == customer.customer_id,
                    CustomerVehicleInterest.vehicle_id == followup.vehicle_id,
                )
            ).scalar_one_or_none()
            if interest:
                interest.next_followup = None
                interest.last_contacted = followup.last_contacted
        self.db.flush()
        return {"followup_id": followup.followup_id, "status": "completed", **decision}

    async def _send_whatsapp_followup(self, followup, customer, auto_send) -> dict:
        vehicle = None
        if followup.vehicle_id:
            vehicle = self.db.get(Vehicle, followup.vehicle_id)
        body = self._build_message(followup, customer, vehicle)
        if not body:
            return {"sent": False, "reason": "no_template"}

        # Always log the outbound attempt (compliance).
        whatsapp_service.log_message(
            self.db, customer.customer_id, "OUTBOUND", content=body,
            channel="WHATSAPP", template_used=followup.message_template or followup.reason
        )

        if not auto_send:
            return {"sent": False, "reason": "auto_send_disabled_queued"}

        from km_car_deals.integrations.whatsapp.client import wa_client
        from km_car_deals.integrations.whatsapp.policy import WhatsAppPolicy

        policy = WhatsAppPolicy(self.db)
        decision = policy.check(customer, is_marketing=True)
        if not decision.allowed:
            return {"sent": False, "reason": f"policy_blocked:{decision.reason}"}

        to = customer.whatsapp_number or customer.phone_number
        if not to:
            return {"sent": False, "reason": "no_number"}
        resp = await wa_client.send_text(to, body)
        return {"sent": True, "response": resp}

    def _build_message(self, followup, customer, vehicle: Optional[Vehicle]) -> Optional[str]:
        template_key = followup.message_template or followup.reason
        template = FOLLOWUP_TEMPLATES.get(template_key)
        if not template:
            return None
        vehicle_name = (vehicle.vehicle_name or vehicle.model) if vehicle else "your car"
        name = customer.name or "there"
        return template.format(name=name, vehicle=vehicle_name)
