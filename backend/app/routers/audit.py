import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db.database import get_session
from app.models import AuditEvent

router = APIRouter(prefix="/audit-events", tags=["audit"])


@router.get("/", response_model=list[AuditEvent])
def list_audit_events(
    entity_type: str | None = Query(default=None),
    entity_id: uuid.UUID | None = Query(default=None),
    actor_email: str | None = Query(default=None),
    action: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[AuditEvent]:
    stmt = select(AuditEvent)

    if entity_type is not None:
        stmt = stmt.where(AuditEvent.entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(AuditEvent.entity_id == entity_id)
    if actor_email is not None:
        stmt = stmt.where(AuditEvent.actor_email == actor_email)
    if action is not None:
        stmt = stmt.where(AuditEvent.action == action)
    if date_from is not None:
        stmt = stmt.where(AuditEvent.occurred_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(AuditEvent.occurred_at <= date_to)

    stmt = stmt.order_by(AuditEvent.occurred_at.desc()).offset(offset).limit(limit)  # type: ignore[arg-type]

    return list(session.exec(stmt).all())
