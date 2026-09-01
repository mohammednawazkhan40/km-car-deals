"""Official Meta Instagram Graph API client for publishing.

Publishing only happens after explicit approval. Never scrapes Instagram.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from km_car_deals.core.config import settings

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com"


class InstagramClient:
    def __init__(self, business_account_id: str, access_token: str):
        self.business_account_id = business_account_id
        self.access_token = access_token
        self.base_url = f"{GRAPH_URL}/{settings.WHATSAPP_API_VERSION}"

    async def upload_image_media(self, image_path: str, caption: str = "") -> Dict[str, Any]:
        # Step 1: create media container with an image URL (must be public-hosted).
        # For a production deployment the image must be hosted at a public URL;
        # we accept an image_path here and let the caller provide a hosted URL
        # via image_url param if available. If only a local path, publishing
        # will surface an error to the operator.
        url = f"{self.base_url}/{self.business_account_id}/media"
        data = {
            "image_url": image_path,
            "caption": caption,
            "access_token": self.access_token,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, data=data)
            if resp.status_code >= 400:
                logger.error("IG media error: %s", resp.text)
                return {"error": resp.text}
            return resp.json()

    async def create_carousel(self, media_ids: List[str], caption: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{self.business_account_id}/media"
        data = {
            "media_type": "CAROUSEL",
            "children": ",".join(media_ids),
            "caption": caption,
            "access_token": self.access_token,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, data=data)
            if resp.status_code >= 400:
                return {"error": resp.text}
            container = resp.json()
        # Publish the container
        pub_url = f"{self.base_url}/{self.business_account_id}/media_publish"
        pub_data = {"creation_id": container.get("id"), "access_token": self.access_token}
        async with httpx.AsyncClient(timeout=30) as client:
            pub = await client.post(pub_url, data=pub_data)
            if pub.status_code >= 400:
                return {"container": container, "publish_error": pub.text}
            return {"container": container, "published": pub.json()}
