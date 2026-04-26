from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Tag


ACTOR_HEADERS = {"x-admin-email": "admin@example.com"}


def _create_tag(client: TestClient, session: Session, name: str) -> str:
    resp = client.post("/api/v1/tags/", json={"name": name}, headers=ACTOR_HEADERS)
    assert resp.status_code == 200
    tag = session.exec(select(Tag).where(Tag.name == name)).first()
    assert tag is not None
    return str(tag.id)


def _question_payload(tag_ids: list[str], prompt: str = "What is EF?") -> dict:
    return {
        "prompt": prompt,
        "explanation": "Normal EF is 55-70%.",
        "tags": [{"id": tag_id} for tag_id in tag_ids],
        "answerChoices": [
            {"text": "55-70%", "is_correct": True},
            {"text": "30-40%", "is_correct": False},
        ],
    }


def test_can_remove_soft_deleted_tag_from_question(
    client: TestClient, session: Session
):
    tag_id = _create_tag(client, session, "Echo")

    create_resp = client.post(
        "/api/v1/questions/",
        json=_question_payload([tag_id]),
        headers=ACTOR_HEADERS,
    )
    assert create_resp.status_code == 200
    question_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/tags/{tag_id}", headers=ACTOR_HEADERS)
    assert delete_resp.status_code == 200

    update_resp = client.put(
        f"/api/v1/questions/{question_id}",
        json=_question_payload([], prompt="Updated EF question"),
        headers=ACTOR_HEADERS,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["tags"] in ([], None)


def test_cannot_attach_deleted_tag_that_was_not_previously_linked(
    client: TestClient, session: Session
):
    active_tag_id = _create_tag(client, session, "Cardiology")
    deleted_tag_id = _create_tag(client, session, "Archived")

    create_resp = client.post(
        "/api/v1/questions/",
        json=_question_payload([active_tag_id]),
        headers=ACTOR_HEADERS,
    )
    assert create_resp.status_code == 200
    question_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/tags/{deleted_tag_id}", headers=ACTOR_HEADERS)
    assert delete_resp.status_code == 200

    update_resp = client.put(
        f"/api/v1/questions/{question_id}",
        json=_question_payload(
            [active_tag_id, deleted_tag_id], prompt="Attempt invalid attach"
        ),
        headers=ACTOR_HEADERS,
    )
    assert update_resp.status_code == 400
    assert "Cannot attach deleted tags" in str(update_resp.json().get("detail", ""))
