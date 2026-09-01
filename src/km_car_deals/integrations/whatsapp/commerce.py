"""Meta WhatsApp Commerce/Catalog API client (official product API)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from km_car_deals.core.config import settings

logger = logging.getLogger(__name__)


class CommerceClient:
    """Interacts with the official Meta WhatsApp commerce catalog endpoints."""

    def __init__(
        self,
        access_token: str,
        business_id: str,
        catalog_id: str,
    ):
        self.access_token = access_token
        self.business_id = business_id
        self.catalog_id = catalog_id
        self.base_url = f"{settings.WHATSAPP_BASE_URL}/{settings.WHATSAPP_API_VERSION}"
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    def _product_payload(self, entry) -> Dict[str, Any]:
        images = []
        if entry.image_url:
            images.append(entry.image_url)
        if entry.additional_images:
            for img in entry.additional_images.values():
                if img and img not in images:
                    images.append(img)
        payload: Dict[str, Any] = {
            "name": entry.title or "Vehicle",
            "description": entry.description or "",
            "video": [],
            "price": entry.price or "0",
            "image_url": images,
            "availability": entry.availability or "out of stock",
            "status": "ACTIVE" if entry.status != "REMOVED" else "INACTIVE",
            "currency": entry.currency or "INR",
            "category": entry.category or "Cars",
            "condition": "Used",
            "brand": "",
        }
        if entry.vehicle_id:
            # stock reference via Retailer ID
            payload["retailer_id"] = entry.vehicle_id
        return payload

    async def create_product(self, entry) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.catalog_id}/products"
        return await self._post(url, self._product_payload(entry))

    async def update_product(self, entry) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.catalog_id}/products/{entry.meta_product_id}"
        return await self._post(url, self._product_payload(entry))

    async def delete_product(self, product_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.catalog_id}/products/{product_id}"
        return await self._delete(url)

    async def _post(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=self._headers)
            if resp.status_code >= 400:
                raise RuntimeError(f"Meta commerce error {resp.status_code}: {resp.text}")
            return resp.json()

    async def _delete(self, url: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.delete(url, headers=self._headers)
            if resp.status_code >= 400:
                raise RuntimeError(f"Meta commerce delete error {resp.status_code}: {resp.text}")
            return resp.json()
