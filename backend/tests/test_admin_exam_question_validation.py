import uuid

from fastapi.testclient import TestClient
from fastapi import Request
from sqlmodel import Session, select

from app.models import AdminExamCreate, Answer_Choice, Exam, ExamCreate, Question, Tag
from app.routers.exams import create_admin_exams, create_exam


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


class _ExecResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _CreateExamSession:
    def __init__(self, question: Question, answer_choices: list[Answer_Choice]):
        self.question = question
        self.answer_choices = answer_choices
        self.exec_calls = 0
        self.exam: Exam | None = None

    def exec(self, _statement):
        self.exec_calls += 1
        if self.exec_calls == 1:
            return _ExecResult([self.question])
        if self.exec_calls == 2:
            return _ExecResult([])
        if self.exec_calls == 3:
            return _ExecResult(self.answer_choices)
        if self.exec_calls == 4:
            return _ExecResult([])
        raise AssertionError(f"Unexpected exec call {self.exec_calls}")

    def add(self, obj):
        if isinstance(obj, Exam):
            self.exam = obj

    def flush(self):
        return None

    def commit(self):
        return None

    def refresh(self, _obj):
        return None


class _CreateAdminExamSession:
    def __init__(self, question: Question, answer_choices: list[Answer_Choice]):
        self.question = question
        self.answer_choices = answer_choices
        self.exec_calls = 0
        self.exams: list[Exam] = []

    def exec(self, _statement):
        self.exec_calls += 1
        if self.exec_calls == 1:
            return _ExecResult([self.question])
        if self.exec_calls == 2:
            return _ExecResult(self.answer_choices)
        if self.exec_calls == 3:
            return _ExecResult([])
        raise AssertionError(f"Unexpected exec call {self.exec_calls}")

    def add(self, obj):
        if isinstance(obj, Exam):
            self.exams.append(obj)

    def get(self, model, key):
        if model is Question and key == self.question.id:
            return self.question
        return None

    def flush(self):
        return None

    def commit(self):
        return None

    def refresh(self, _obj):
        return None


def test_create_exam_accepts_tutor():
    question = Question(
        id=uuid.uuid4(),
        prompt="Visibility question",
        explanation="Explanation",
    )
    answer_choice = Answer_Choice(
        id=uuid.uuid4(),
        question_id=question.id,
        text="Correct",
        is_correct=True,
    )
    session = _CreateExamSession(question, [answer_choice])

    response = create_exam(
        session=session,
        exam_in=ExamCreate(
            member_id="member-1",
            question_count=1,
            tutor=True,
            filters=["unanswered"],
        ),
    )

    assert response.tutor is True
    assert session.exam is not None
    assert session.exam.tutor is True


def test_create_admin_exam_accepts_tutor():
    question = Question(
        id=uuid.uuid4(),
        prompt="Visibility question",
        explanation="Explanation",
    )
    answer_choice = Answer_Choice(
        id=uuid.uuid4(),
        question_id=question.id,
        text="Correct",
        is_correct=True,
    )
    session = _CreateAdminExamSession(question, [answer_choice])
    request = Request({"type": "http", "headers": []})
    request.state.request_id = "req-1"
    request.state.actor_email = "admin@example.com"

    response = create_admin_exams(
        session=session,
        request=request,
        exam_in=AdminExamCreate(
            member_uuids=["member-2"],
            question_ids=[str(question.id)],
            tutor=True,
        ),
    )

    assert response[0].tutor is True
    assert session.exams
    assert session.exams[0].tutor is True
