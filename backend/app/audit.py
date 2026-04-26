from dataclasses import dataclass
from typing import Any
import uuid

from fastapi import Request
from sqlmodel import Session

from app.models import AuditEvent

X_ACTOR_EMAIL_HEADER = "x-admin-email"
X_REQUEST_ID_HEADER = "x-request-id"


@dataclass
class AuditContext:
    request_id: str | None
    actor_email: str | None
    actor_source: str


def get_audit_context(request: Request) -> AuditContext:
    request_id = getattr(request.state, "request_id", None)
    actor_email = getattr(request.state, "actor_email", None)

    return AuditContext(
        request_id=request_id,
        actor_email=actor_email,
        actor_source="header" if actor_email else "unknown",
    )


def extract_actor_email(request: Request) -> str | None:
    actor_email = request.headers.get(X_ACTOR_EMAIL_HEADER)
    if not actor_email:
        return None
    normalized = actor_email.strip().lower()
    return normalized or None


def extract_request_id(request: Request) -> str:
    request_id = request.headers.get(X_REQUEST_ID_HEADER)
    if request_id:
        return request_id.strip()
    return str(uuid.uuid4())


def record_audit_event(
    session: Session,
    *,
    context: AuditContext,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    audit_event = AuditEvent(
        request_id=context.request_id,
        actor_email=context.actor_email,
        actor_source=context.actor_source,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before,
        after_json=after,
        metadata_json=metadata,
    )
    session.add(audit_event)
