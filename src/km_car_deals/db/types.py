"""Portable JSON column type.

Uses PostgreSQL JSONB in production and generic JSON elsewhere (e.g. SQLite
for tests/migrations), so the models compile and test cleanly on any backend.
"""

from __future__ import annotations

from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


class JsonType(TypeDecorator):
    """Maps to JSONB on PostgreSQL and JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB

            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
