"""Audit log service — records every AI and dealer action.

Usage:
    from km_car_deals.services.audit import log_action
    log_action(db, actor="admin", action="VEHICLE_APPROVED",
               entity_type="Vehicle", entity_id=vehicle.vehicle_id,
               before_data={"status": "NEEDS_REVIEW"},
               after_data={"status": "DEALER_APPROVED"})
    db.flush()  # caller commits
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from km_car_deals.core.logging import get_logger
from km_car_deals.models.vehicle import AppAuditLog

logger = get_logger(__name__)


def log_action(
    db: Session,
    action: str,
    *,
    actor: Optional[str] = "system",
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    before_data: Optional[Dict[str, Any]] = None,
    after_data: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AppAuditLog:
    """Write one audit log entry and flush to the session (not committed)."""
    entry = AppAuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_data=before_data,
        after_data=after_data,
        notes=notes,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    db.flush()
    logger.info("AUDIT %s | actor=%s | %s/%s", action, actor, entity_type, entity_id)
    return entry


def get_logs(
    db: Session,
    entity_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    actor: Optional[str] = None,
    limit: int = 100,
) -> List[AppAuditLog]:
    """Query audit logs with optional filters."""
    q = select(AppAuditLog).order_by(AppAuditLog.created_at.desc()).limit(limit)
    if entity_id:
        q = q.where(AppAuditLog.entity_id == entity_id)
    if entity_type:
        q = q.where(AppAuditLog.entity_type == entity_type)
    if action:
        q = q.where(AppAuditLog.action == action)
    if actor:
        q = q.where(AppAuditLog.actor == actor)
    return list(db.execute(q).scalars())
