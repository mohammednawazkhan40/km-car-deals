"""AI provider abstraction.

Provides pluggable OCR, vision, image, and LLM services.
Each provider is gated by a feature flag and configured via env vars.
When a feature is disabled, callers fall back to deterministic logic so the
application remains fully functional in offline/demo mode.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from km_car_deals.core.config import settings
from km_car_deals.core.logging import get_logger

logger = get_logger(__name__)


class AIProvider:
    """Base interface each provider implements."""

    name: str = "base"

    def ocr_text(self, file_path: str) -> str:
        raise NotImplementedError

    def extract_rc_fields(self, text: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def analyze_photo(self, file_path: str) -> Dict[str, Any]:
        raise NotImplementedError

    def classify_photo(self, file_path: str) -> str:
        raise NotImplementedError

    def process_image_background(
        self, file_path: str, background: str, output_path: str
    ) -> bool:
        raise NotImplementedError

    def complete_llm(
        self, prompt: str, system: str = "", json_mode: bool = False
    ) -> str:
        raise NotImplementedError


class DisabledProvider(AIProvider):
    """Used when AI features are disabled; returns empty/neutral results."""

    name = "disabled"

    def ocr_text(self, file_path: str) -> str:
        logger.warning("OCR disabled - returning empty text for %s", file_path)
        return ""

    def extract_rc_fields(self, text: str) -> List[Dict[str, Any]]:
        return []

    def analyze_photo(self, file_path: str) -> Dict[str, Any]:
        return {"quality_score": None, "category": None, "notes": "AI vision disabled."}

    def classify_photo(self, file_path: str) -> str:
        return "other"

    def process_image_background(
        self, file_path: str, background: str, output_path: str
    ) -> bool:
        return False

    def complete_llm(
        self, prompt: str, system: str = "", json_mode: bool = False
    ) -> str:
        return ""


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self) -> None:
        try:
            import openai  # type: ignore
        except ImportError as exc:  # pragma: no cover - missing optional SDK
            raise NoAIProviderSdk("openai SDK not installed") from exc
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def ocr_text(self, file_path: str) -> str:
        import base64

        with open(file_path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        resp = self.client.chat.completions.create(
            model=settings.OPENAI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract ALL text from this vehicle registration "
                                "certificate or document. Return only the raw text "
                                "with field labels."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                    ],
                }
            ],
        )
        return resp.choices[0].message.content or ""

    def extract_rc_fields(self, text: str) -> List[Dict[str, Any]]:
        from km_car_deals.ai.prompts import RC_EXTRACTION_PROMPT
        import json

        raw = self.complete_llm(
            RC_EXTRACTION_PROMPT.format(rc_text=text), json_mode=True
        )
        try:
            data = json.loads(raw)
            return data if isinstance(data, list) else []
        except Exception:
            logger.error("Failed to parse RC extraction JSON from OpenAI")
            return []

    def analyze_photo(self, file_path: str) -> Dict[str, Any]:
        import base64, json

        with open(file_path, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode()
        resp = self.client.chat.completions.create(
            model=settings.OPENAI_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this vehicle photo. Return JSON with keys: "
                                "category (front/rear/left/right/interior/dashboard/"
                                "odometer/engine/boot/wheel/tyre/other), quality_score (0-1), "
                                "blur_detected (bool), lighting_ok (bool), composed_ok (bool), "
                                "damage_found (list of dicts {type, part, confidence} or empty), "
                                "notes. Never invent damage."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                        },
                    ],
                }
            ],
        )
        try:
            return json.loads(resp.choices[0].message.content)
        except Exception:
            return {"notes": "Could not parse vision JSON."}

    def classify_photo(self, file_path: str) -> str:
        return self.analyze_photo(file_path).get("category", "other")

    def process_image_background(
        self, file_path: str, background: str, output_path: str
    ) -> bool:
        try:
            from km_car_deals.image_processing.processor import replace_background

            return replace_background(file_path, background, output_path)
        except Exception:
            return False

    def complete_llm(
        self, prompt: str, system: str = "", json_mode: bool = False
    ) -> str:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        resp = self.client.chat.completions.create(
            model=settings.OPENAI_MODEL, messages=msgs
        )
        return resp.choices[0].message.content or ""


class GeminiProvider(AIProvider):
    name = "gemini"

    def _model(self):
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:  # pragma: no cover - missing optional SDK
            raise NoAIProviderSdk("google-generativeai SDK not installed") from exc
        genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
        return genai.GenerativeModel(settings.GEMINI_MODEL)

    def complete_llm(
        self, prompt: str, system: str = "", json_mode: bool = False
    ) -> str:
        model = self._model()
        full = f"{system}\n\n{prompt}" if system else prompt
        resp = model.generate_content(full)
        return resp.text or ""

    def extract_rc_fields(self, text: str) -> List[Dict[str, Any]]:
        from km_car_deals.ai.prompts import RC_EXTRACTION_PROMPT
        import json, re

        raw = self.complete_llm(RC_EXTRACTION_PROMPT.format(rc_text=text))
        m = re.search(r"\[.*\]", raw, re.S)
        if not m:
            return []
        try:
            data = json.loads(m.group(0))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def ocr_text(self, file_path: str) -> str:
        from km_car_deals.ai.ocr import ocr_file_local

        try:
            return ocr_file_local(file_path)
        except Exception:
            return ""

    def analyze_photo(self, file_path: str) -> Dict[str, Any]:
        return {"notes": "Gemini offline vision not implemented."}

    def classify_photo(self, file_path: str) -> str:
        from km_car_deals.ai.vision import classify_photo_local

        return classify_photo_local(file_path)

    def process_image_background(
        self, file_path: str, background: str, output_path: str
    ) -> bool:
        try:
            from km_car_deals.image_processing.processor import replace_background

            return replace_background(file_path, background, output_path)
        except Exception:
            return False


class NoAIProviderSdk(Exception):
    """Raised when a provider SDK is not installed but was requested."""


def get_ai_provider() -> AIProvider:
    """Return the configured AI provider, or DisabledProvider if not usable."""
    if settings.AI_LLM_ENABLED and settings.GOOGLE_GEMINI_API_KEY:
        try:
            return GeminiProvider()
        except NoAIProviderSdk:
            logger.warning("Gemini SDK missing; falling back to disabled provider")
    if settings.AI_LLM_ENABLED and settings.OPENAI_API_KEY:
        try:
            return OpenAIProvider()
        except NoAIProviderSdk:
            logger.warning("OpenAI SDK missing; falling back to disabled provider")
    if settings.OPENAI_API_KEY:
        try:
            return OpenAIProvider()
        except NoAIProviderSdk:
            logger.warning("OpenAI SDK missing; falling back to disabled provider")
    return DisabledProvider()


# A lazy proxy so providers are resolved on first use (never at import time).
class _LazyProvider:
    def __getattr__(self, name):
        provider = get_ai_provider()
        return getattr(provider, name)


ai_provider: AIProvider = _LazyProvider()  # type: ignore
