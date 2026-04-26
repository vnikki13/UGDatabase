"""
Tests that audit events are recorded for tag mutations.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import AuditEvent, Tag


ACTOR_EMAIL = "admin@example.com"
ACTOR_HEADERS = {"x-admin-email": ACTOR_EMAIL}


def _create_tag_and_get_id(client: TestClient, session: Session, name: str) -> str:
    resp = client.post("/api/v1/tags/", json={"name": name}, headers=ACTOR_HEADERS)
    assert resp.status_code == 200
    tag = session.exec(select(Tag).where(Tag.name == name)).first()
    assert tag is not None
    return str(tag.id)


def test_create_tag_records_audit_event(client: TestClient, session: Session):
    resp = client.post(
        "/api/v1/tags/", json={"name": "Cardiology"}, headers=ACTOR_HEADERS
    )
    assert resp.status_code == 200

    events = session.exec(
        select(AuditEvent).where(AuditEvent.action == "tag.create")
    ).all()
    assert len(events) == 1
    event = events[0]
    assert event.actor_email == ACTOR_EMAIL
    assert event.entity_type == "tag"
    assert event.before_json is None
    assert event.after_json is not None
    assert event.after_json["name"] == "Cardiology"


def test_update_tag_records_audit_event(client: TestClient, session: Session):
    tag_id = _create_tag_and_get_id(client, session, "OldName")

    resp = client.put(
        f"/api/v1/tags/{tag_id}",
        json={"name": "NewName"},
        headers=ACTOR_HEADERS,
    )
    assert resp.status_code == 200

    events = session.exec(
        select(AuditEvent).where(AuditEvent.action == "tag.update")
    ).all()
    assert len(events) == 1
    event = events[0]
    assert event.actor_email == ACTOR_EMAIL
    assert event.before_json is not None
    assert event.before_json["name"] == "OldName"
    assert event.after_json is not None
    assert event.after_json["name"] == "NewName"


def test_delete_tag_records_audit_event(client: TestClient, session: Session):
    tag_id = _create_tag_and_get_id(client, session, "ToDelete")

    resp = client.delete(f"/api/v1/tags/{tag_id}", headers=ACTOR_HEADERS)
    assert resp.status_code == 200

    events = session.exec(
        select(AuditEvent).where(AuditEvent.action == "tag.delete")
    ).all()
    assert len(events) == 1
    event = events[0]
    assert event.actor_email == ACTOR_EMAIL
    assert event.before_json is not None
    assert event.before_json["name"] == "ToDelete"
    assert event.before_json["deleted_at"] is None
    # Soft delete: after_json reflects the tag with deleted_at set
    assert event.after_json is not None
    assert event.after_json["deleted_at"] is not None


def test_audit_read_endpoint_filters_by_entity(client: TestClient, session: Session):
    client.post("/api/v1/tags/", json={"name": "FilterMe"}, headers=ACTOR_HEADERS)

    events_resp = client.get("/api/v1/audit-events/?entity_type=tag")
    assert events_resp.status_code == 200
    events = events_resp.json()
    assert len(events) >= 1
    assert all(e["entity_type"] == "tag" for e in events)
