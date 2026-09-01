"""WhatsApp Sales Agent - orchestrates inbound WhatsApp messages.

Flow: parse payload -> identify customer -> log inbound -> run conversation
agent -> send (policy-gated) reply -> record outbound.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from km_car_deals.agents.sales_conversation_agent import SalesConversationAgent
from km_car_deals.core.logging import get_logger
from km_car_deals.integrations.whatsapp import service as whatsapp_service
from km_car_deals.models.customer import Customer
from km_car_deals.services import crm

logger = get_logger(__name__)


class WhatsAppSalesAgent:
    def __init__(self, db: Session):
        self.db = db

    async def handle_webhook_entry(self, entry: dict) -> List[Dict[str, Any]]:
        """Process a webhook entry (array of changes)."""
        results: List[Dict[str, Any]] = []
        for change in entry.get("changes", []) or []:
            if change.get("field") != "messages":
                continue
            value = change.get("value", {})
            for msg in value.get("messages", []) or []:
                results.append(await self._handle_message(value, msg))
        return results

    async def _handle_message(self, value: dict, msg: dict) -> Dict[str, Any]:
        """Handle a single inbound message."""
        from_number = msg.get("from")
        if not from_number:
            return {"handled": False, "reason": "no_from"}

        # Contact profile (name) if present
        profile_name = None
        contacts = value.get("contacts", []) or []
        if contacts:
            profile_name = contacts[0].get("profile", {}).get("name")

        customer, created = crm.get_or_create_customer(
            self.db, whatsapp=from_number, name=profile_name, source="WHATSAPP"
        )
        if created:
            customer.lead_status = "NEW"

        text = self._message_text(msg)
        media = self._message_media(msg)

        # Always log the inbound message first (also handles STOP/consent).
        whatsapp_service.log_message(
            self.db, customer.customer_id, "INBOUND",
            content=text or None, channel="WHATSAPP",
            meta_message_id=msg.get("id"), media_type=media,
        )

        # Escape hatch: if the customer opted out via this message, don't reply.
        if text and self._is_stop(text):
            return {"handled": True, "customer_id": customer.customer_id, "opted_out": True}

        # If a customer sent an image/document without text, treat as intake/intent.
        if not text and media:
            text = self._classify_media_message(media)

        agent = SalesConversationAgent(self.db)
        result = agent.handle(customer, text or "")

        # Persist interaction/interest metadata
        self.db.flush()

        # Attempt to send reply (policy-gated)
        send_result = await whatsapp_service.send_text_message(
            self.db, customer, result.reply, is_marketing=False
        )

        return {
            "handled": True,
            "customer_id": customer.customer_id,
            "reply": result.reply,
            "handoff": result.handoff,
            "handoff_reason": result.handoff_reason,
            "followup": result.followup_create,
            "send": send_result,
        }

    def _message_text(self, msg: dict) -> Optional[str]:
        if msg.get("type") == "text":
            return msg.get("text", {}).get("body")
        return None

    def _message_media(self, msg: dict) -> Optional[str]:
        for kind in ("image", "document", "video", "audio", "location", "contacts"):
            if msg.get("type") == kind:
                return kind
        return None

    def _classify_media_message(self, media: str) -> str:
        if media == "image":
            return "send photos"
        if media == "document":
            return "send details"
        if media == "location":
            return "where is the showroom"
        return ""

    def _is_stop(self, text: str) -> bool:
        lowered = text.strip().lower()
        return any(
            kw in lowered for kw in ("stop", "unsubscribe", "opt out", "don't contact", "do not contact")
        )
