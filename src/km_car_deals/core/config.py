"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration.

    All secrets are read from environment variables / .env file.
    Nothing is hard-coded.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General ---
    APP_NAME: str = "KM Car Deals AI Agent"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_PREFIX: str = "/api/v1"

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/km_car_deals"
    )

    # --- WhatsApp Business API ---
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_API_VERSION: str = "v20.0"
    WHATSAPP_BASE_URL: str = "https://graph.facebook.com"

    # --- WhatsApp Meta Catalog (Commerce) ---
    META_WA_CATALOG_ID: str = ""
    META_WA_BUSINESS_ID: str = ""

    # Approved outbound template name (for template-required messages)
    WHATSAPP_TEMPLATE: str = ""

    # --- Instagram / Meta Graph ---
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = ""
    INSTAGRAM_ACCESS_TOKEN: str = ""
    INSTAGRAM_PAGE_ID: str = ""

    # --- AI providers (optional, feature flags) ---
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_VISION_MODEL: str = "gpt-4o"

    GOOGLE_GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # Image background options - allow selection
    DEFAULT_BACKGROUND: str = "premium_showroom"

    # --- AI Feature flags (so app runs without paid keys) ---
    AI_OCR_ENABLED: bool = False
    AI_VISION_ENABLED: bool = False
    AI_IMAGE_ENABLED: bool = False
    AI_LLM_ENABLED: bool = False

    # --- Follow-up / messaging policy ---
    MAX_MESSAGES_PER_DAY: int = 3
    MINIMUM_FOLLOWUP_INTERVAL_HOURS: float = 24.0
    QUIET_HOURS_START: str = "22:00"
    QUIET_HOURS_END: str = "08:00"
    BUSINESS_HOURS_START: str = "09:00"
    BUSINESS_HOURS_END: str = "20:00"
    SEND_MESSAGES_AUTOMATICALLY: bool = False

    # --- Storage ---
    UPLOAD_DIR: str = "data/uploads"
    EXPORT_DIR: str = "data/exports"

    # --- CORS ---
    CORS_ORIGINS: str = "*"

    # --- Public access control ---
    PUBLIC_API_REQUIRES_KEY: bool = False
    PUBLIC_API_KEY: str = ""

    # --- Business / Dealer defaults (seeded into BusinessSettings on first run) ---
    DEALER_NAME: str = "KM Car Deals"
    DEALER_TAGLINE: str = "Your Trusted Pre-Owned Car Destination"
    DEALER_ADDRESS_LINE1: str = "Opp. Hyundai Showroom, Humnabad Road"
    DEALER_ADDRESS_LINE2: str = "Kapnoor"
    DEALER_CITY: str = "Kalaburagi"
    DEALER_STATE: str = "Karnataka"
    DEALER_PINCODE: str = "585104"
    DEALER_PHONE_PRIMARY: str = ""
    DEALER_PHONE_SECONDARY: str = ""
    DEALER_WHATSAPP: str = ""
    DEALER_EMAIL: str = ""
    DEALER_WEBSITE: str = "www.kmcardeals.com"
    DEALER_GOOGLE_MAPS_URL: str = ""
    DEALER_AUTO_PUBLISH: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return v
        return v

    @property
    def cors_origin_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()


settings = get_settings()
