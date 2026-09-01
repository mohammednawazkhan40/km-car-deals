"""Database engine, session, and declarative base.

The engine is created lazily from `get_database_url()` so tests can override
the backend (e.g. SQLite) by calling `configure_test_engine()` before use.
"""

from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from km_car_deals.core.config import settings

logger = logging.getLogger(__name__)

_database_url: str = settings.DATABASE_URL


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _build_engine(url: str) -> Engine:
    """Create an Engine for the given database URL with sensible defaults."""
    kwargs = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        # SQLite needs a check_same_thread override for FastAPI/test usage.
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine: Engine = _build_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)


def override_engine(url: str = None, create_tables: bool = True) -> None:
    """Swap the engine/session to a different backend (used by tests).

    Defaults to an in-memory SQLite database for tests. When ``create_tables``
    is True, all tables registered on the shared ``Base`` are created.
    """
    global engine, SessionLocal
    target = url or "sqlite:///:memory:"
    engine = _build_engine(target)
    SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        future=True,
    )
    if create_tables:
        import km_car_deals.models  # noqa: F401  (register all models)

        metadata = (
            engine._metadata  # noqa: SLF001
            if hasattr(engine, "_metadata")
            else None
        )
        Base.metadata.create_all(engine)


def get_db():
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()