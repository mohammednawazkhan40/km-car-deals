"""WhatsApp messaging policy enforcement.

Governs consent, opt-in/out, conversation window, quiet hours, and frequency
limits. Used before any outbound message is sent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from km_car_deals.core.config import settings
from km_car_deals.core.logging import get_logger
from km_car_deals.models.customer import Customer, CustomerMessage

logger = get_logger(__name__)


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    should_use_template: bool = False


def _now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(s: str) -> time:
    try:
        h, m = s.split(":")
        return time(int(h), int(m))
    except Exception:
        return time(0, 0)


class WhatsAppPolicy:
    """Evaluates whether an outbound message is permitted."""

    def __init__(self, db: Session):
        self.db = db

    def check(
        self, customer: Customer, *, is_marketing: bool = True,
        allow_outside_hours: bool = False
    ) -> PolicyDecision:
        """Evaluate policy for sending a message to `customer`."""
        # Consent
        if customer.opt_out:
            return PolicyDecision(False, "customer_opted_out")

        # Conversation window: if the customer messaged us recently we can
        # reply within the 24-hour customer-service window without a template.
        window_open = self._is_window_open(customer)
        if window_open:
            return PolicyDecision(True, "conversation_window_open")

        if is_marketing:
            # Marketing outside window requires an approved template.
            if not self._already_sent_template_recently(customer):
                return PolicyDecision(
                    False, "template_required_for_marketing", should_use_template=True
                )

        # Quiet hours
        if not allow_outside_hours and self._in_quiet_hours(_now()):
            return PolicyDecision(False, "quiet_hours")

        # Frequency limits
        if self._messages_today(customer) >= settings.MAX_MESSAGES_PER_DAY:
            return PolicyDecision(False, "max_messages_per_day_reached")

        # Minimum interval between follow-ups
        if not self._respects_min_interval(customer):
            return PolicyDecision(False, "minimum_followup_interval")

        return PolicyDecision(True, "policy_ok")

    def _is_window_open(self, customer: Customer) -> bool:
        last_in = customer.last_inbound_at
        if not last_in:
            return False
        # WhatsApp 24h customer service window
        return _now() - last_in < timedelta(hours=24)

    def _in_quiet_hours(self, now: datetime) -> bool:
        quiet_start = parse_time(settings.QUIET_HOURS_START)
        quiet_end = parse_time(settings.QUIET_HOURS_END)
        current = now.astimezone().time().replace(tzinfo=None)
        if quiet_start <= quiet_end:
            return quiet_start <= current < quiet_end
        # overnight window, e.g. 22:00 -> 08:00
        return current >= quiet_start or current < quiet_end

    def _messages_today(self, customer: Customer) -> int:
        start = _now().replace(hour=0, minute=0, second=0, microsecond=0)
        return (
            self.db.execute(
                select(CustomerMessage).where(
                    CustomerMessage.customer_id == customer.customer_id,
                    CustomerMessage.direction == "OUTBOUND",
                    CustomerMessage.sent_at >= start,
                )
            )
            .scalars()
            .all().__len__()
        )

    def _respects_min_interval(self, customer: Customer) -> bool:
        last_sent = customer.last_outbound_at
        if not last_sent:
            return True
        interval = settings.MINIMUM_FOLLOWUP_INTERVAL_HOURS
        return _now() - last_sent >= timedelta(hours=interval)

    def _already_sent_template_recently(self, customer: Customer) -> bool:
        # A recently sent approved template resets our ability to message.
        last_sent = customer.last_outbound_at
        if not last_sent:
            return False
        return _now() - last_sent < timedelta(hours=24)
