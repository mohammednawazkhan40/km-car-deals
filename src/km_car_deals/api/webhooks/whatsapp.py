"""WhatsApp webhook endpoints and stock availability status (verification)."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy.orm import Session

from km_car_deals.agents.whatsapp_sales_agent import WhatsAppSalesAgent
from km_car_deals.core.config import settings
from km_car_deals.core.logging import get_logger
from km_car_deals.db.session import get_db

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_signature(payload: bytes, signature: str | None) -> bool:
    """Verify the X-Hub-Signature-256 header."""
    if not settings.WHATSAPP_ACCESS_TOKEN:
        # No token configured -> accept (dev mode), but still require verify path.
        return True
    if not signature or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        settings.WHATSAPP_ACCESS_TOKEN.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.get("/whatsapp")
def verify_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify.token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
):
    """WhatsApp GET verification endpoint."""
    verify_token = settings.WHATSAPP_VERIFY_TOKEN
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        return int(hub_challenge) if hub_challenge else ""
    return {"error": "Verification failed"}


@router.post("/whatsapp")
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
):
    """WhatsApp POST webhook endpoint for inbound events."""
    body = await request.body()
    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(401, "Invalid signature")

    import json

    try:
        payload = json.loads(body)
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    agent = WhatsAppSalesAgent(db)
    results: List[Dict[str, Any]] = []
    sent_intake = False
    for entry in payload.get("entry", []):
        try:
            res = await agent.handle_webhook_entry(entry)
            results.extend(res)
        except Exception:
            logger.exception("Webhook handling error")
    db.commit()

    # If the inbound contained images (vehicle intake), a human/agent flow can
    # pick them up in a follow-up job; the sales agent already handled text.
    return {"status": "received", "handled": len(results)}
