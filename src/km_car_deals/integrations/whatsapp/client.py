"""WhatsApp Business Platform API client (Meta Graph API).

Uses the official API only. Credentials come from env vars, never hard-coded.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from km_car_deals.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppApiClient:
    """Thin, typed client around the WhatsApp Business Cloud API."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
    ):
        self.access_token = access_token or settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
        self.base_url = f"{settings.WHATSAPP_BASE_URL}/{settings.WHATSAPP_API_VERSION}"
        self._headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    @property
    def configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    async def send_text(self, to: str, body: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        return await self._post(url, payload)

    async def send_image(self, to: str, link: str, caption: str = "") -> Dict[str, Any]:
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": link, "caption": caption},
        }
        return await self._post(url, payload)

    async def send_template(
        self,
        to: str,
        template_name: str,
        language: str = "en",
        components: Optional[list] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }
        if components:
            payload["template"]["components"] = components
        return await self._post(url, payload)

    async def _post(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.configured:
            raise RuntimeError("WhatsApp API is not configured (missing credentials).")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=self._headers)
            if resp.status_code >= 400:
                logger.error("WhatsApp API error %s: %s", resp.status_code, resp.text)
                raise WhatsAppApiError(resp.status_code, resp.text)
            return resp.json()


class WhatsAppApiError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"WhatsApp API error {status_code}: {body}")


wa_client = WhatsAppApiClient()
