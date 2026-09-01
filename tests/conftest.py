"""Shared pytest fixtures for Phase 1 tests.

Uses an in-memory SQLite engine so tests run without PostgreSQL. All models are
registered on the shared Base so foreign keys resolve.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from km_car_deals.core.config import settings
from km_car_deals.db.session import override_engine
import km_car_deals.models  # noqa: F401  (register all models on Base)


@pytest.fixture(scope="session", autouse=True)
def _sqlite_backend():
    """Force an in-memory SQLite backend for the whole test session."""
    override_engine("sqlite://")
    yield


@pytest.fixture(scope="function")
def db(_sqlite_backend):
    from km_car_deals.db.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def tmp_storage(tmp_path: pathlib.Path) -> pathlib.Path:
    """A temp directory standing in for settings storage dirs."""
    return tmp_path


@pytest.fixture()
def seed_vehicle_facts() -> dict:
    return {
        "manufacturer": {"value": "Hyundai", "source": "user", "confidence": 0.9},
        "vehicle_model": {"value": "Creta", "source": "user", "confidence": 0.9},
        "manufacturing_year": {"value": 2022, "source": "user", "confidence": 1.0},
        "fuel_type": {"value": "DIESEL", "source": "user", "confidence": 1.0},
    }