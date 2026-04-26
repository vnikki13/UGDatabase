"""
Tests that audit events are recorded for question mutations.
"""

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import AuditEvent, Tag


ACTOR_EMAIL = "admin@example.com"
ACTOR_HEADERS = {"x-admin-email": ACTOR_EMAIL}


def _create_tag(client: TestClient, session: Session, name: str) -> str:
    resp = client.post("/api/v1/tags/", json={"name": name}, headers=ACTOR_HEADERS)
    assert resp.status_code == 200
    tag = session.exec(select(Tag).where(Tag.name == name)).first()
    assert tag is not None
    return tag.name


def _question_payload(tag_name: str) -> dict:
    return {
        "prompt": "What is the normal ejection fraction?",
        "explanation": "Normal EF is 55-70%.",
        "tags": [{"name": tag_name}],
        "answerChoices": [
            {"text": "55-70%", "is_correct": True},
            {"text": "30-40%", "is_correct": False},
        ],
    }


def test_create_question_records_audit_event(client: TestClient, session: Session):
    tag_name = "Echo"
    _create_tag(client, session, tag_name)

    resp = client.post(
        "/api/v1/questions/", json=_question_payload(tag_name), headers=ACTOR_HEADERS
    )
    assert resp.status_code == 200

    events = session.exec(
        select(AuditEvent).where(AuditEvent.action == "question.create")
    ).all()
    assert len(events) == 1
    event = events[0]
    assert event.actor_email == ACTOR_EMAIL
    assert event.entity_type == "question"
    assert event.before_json is None
    assert event.after_json is not None
    assert event.after_json["prompt"] == "What is the normal ejection fraction?"


def test_update_question_records_audit_event_with_versioning(
    client: TestClient, session: Session
):
    tag_name = "Vascular"
    _create_tag(client, session, tag_name)

    create_resp = client.post(
        "/api/v1/questions/", json=_question_payload(tag_name), headers=ACTOR_HEADERS
    )
    original_id = create_resp.json()["id"]

    updated_payload = {
        **_question_payload(tag_name),
        "prompt": "Updated: What is EF?",
    }
    update_resp = client.put(
        f"/api/v1/questions/{original_id}", json=updated_payload, headers=ACTOR_HEADERS
    )
    assert update_resp.status_code == 200

    events = session.exec(
        select(AuditEvent).where(AuditEvent.action == "question.update")
    ).all()
    assert len(events) == 1
    event = events[0]
    assert event.actor_email == ACTOR_EMAIL
    # Before snapshot should be the original prompt
    assert event.before_json is not None
    assert event.before_json["prompt"] == "What is the normal ejection fraction?"
    # Metadata should contain versioning info
    assert event.metadata_json is not None
    assert "previous_question_id" in event.metadata_json


def test_soft_delete_question_records_audit_event(client: TestClient, session: Session):
    tag_name = "Renal"
    _create_tag(client, session, tag_name)

    create_resp = client.post(
        "/api/v1/questions/", json=_question_payload(tag_name), headers=ACTOR_HEADERS
    )
    question_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/questions/{question_id}", headers=ACTOR_HEADERS)
    assert del_resp.status_code == 200

    events = session.exec(
        select(AuditEvent).where(AuditEvent.action == "question.delete")
    ).all()
    assert len(events) == 1
    event = events[0]
    assert event.actor_email == ACTOR_EMAIL
    assert event.before_json is not None
    assert event.before_json["deleted_at"] is None
    # Soft delete: after_json reflects the question with deleted_at set
    assert event.after_json is not None
    assert event.after_json["deleted_at"] is not None
    assert event.metadata_json == {"delete_type": "soft"}
