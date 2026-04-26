import uuid

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


def test_admin_exam_rejects_deleted_questions(client: TestClient, session: Session):
    tag_id = _create_tag(client, session, "AdminExamTag")

    create_question_resp = client.post(
        "/api/v1/questions/",
        json=_question_payload([tag_id], prompt="Question to be deleted"),
        headers=ACTOR_HEADERS,
    )
    assert create_question_resp.status_code == 200
    question_id = create_question_resp.json()["id"]

    delete_question_resp = client.delete(
        f"/api/v1/questions/{question_id}", headers=ACTOR_HEADERS
    )
    assert delete_question_resp.status_code == 200

    create_exam_resp = client.post(
        "/api/v1/exams/admin",
        json={"member_uuids": ["member-1"], "question_ids": [question_id]},
        headers=ACTOR_HEADERS,
    )

    assert create_exam_resp.status_code == 400
    assert "Deleted questions cannot be used in exams" in str(
        create_exam_resp.json().get("detail", "")
    )


def test_admin_exam_rejects_unknown_questions(client: TestClient):
    missing_question_id = str(uuid.uuid4())

    create_exam_resp = client.post(
        "/api/v1/exams/admin",
        json={"member_uuids": ["member-1"], "question_ids": [missing_question_id]},
        headers=ACTOR_HEADERS,
    )

    assert create_exam_resp.status_code == 400
    assert "Questions do not exist" in str(create_exam_resp.json().get("detail", ""))
