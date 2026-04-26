from datetime import datetime, UTC
from typing import Any, List
import uuid
from sqlalchemy import ARRAY, Column, String, JSON
from sqlmodel import Field, SQLModel


# Questions
class TagBase(SQLModel):
    name: str


class Tag(TagBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.now().astimezone().tzinfo)
    )
    updated_at: datetime | None = Field(default=None)
    deleted_at: datetime | None = Field(default=None)


class TagCreate(TagBase):
    pass


class TagUpdate(TagBase):
    pass


class Tags(SQLModel):
    data: list[Tag]
    count: int


class Question_Tag(SQLModel, table=True):
    question_id: uuid.UUID = Field(
        foreign_key="question.id", primary_key=True, ondelete="CASCADE"
    )
    tag_id: uuid.UUID = Field(foreign_key="tag.id", primary_key=True)


class Exam_Tag(SQLModel, table=True):
    exam_id: uuid.UUID = Field(
        foreign_key="exam.id", primary_key=True, ondelete="CASCADE"
    )
    tag_id: uuid.UUID = Field(foreign_key="tag.id", primary_key=True)


class QuestionBase(SQLModel):
    prompt: str
    media_content_type: str | None = Field(default=None)
    explanation: str | None = Field(default=None)


class Question(QuestionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    version: int = Field(default=1)
    base_question_id: uuid.UUID | None = Field(default=None, foreign_key="question.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.now().astimezone().tzinfo)
    )
    updated_at: datetime | None = Field(default=None)
    deleted_at: datetime | None = Field(default=None)


class AnswerChoiceBase(SQLModel):
    text: str
    is_correct: bool


class Answer_Choice(AnswerChoiceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    question_id: uuid.UUID = Field(foreign_key="question.id", ondelete="CASCADE")


class QuestionCreate(QuestionBase):
    tags: list[TagBase] | None = Field(default=None)
    answerChoices: list[AnswerChoiceBase]


# Response Models
class AnswerChoiceResponse(SQLModel):
    id: uuid.UUID
    text: str
    is_correct: bool


class QuestionRead(QuestionBase):
    id: uuid.UUID
    tags: list[TagBase] | None = Field(default=None)
    answerChoices: list[AnswerChoiceResponse]
    deleted_at: datetime | None = None


class QuestionReadWithUserAnswer(QuestionBase):
    id: uuid.UUID
    tags: list[TagBase] | None = Field(default=None)
    answerChoices: list[AnswerChoiceResponse]
    user_answer_id: uuid.UUID | None = None
    deleted_at: datetime | None = None


class QuestionUpdate(QuestionBase):
    prompt: str | None = None
    tags: list[TagBase] | None = None
    answerChoices: list[AnswerChoiceBase] | None = None


class Questions(SQLModel):
    data: list[QuestionRead]
    count: int


class QuestionCreateResponse(QuestionRead):
    upload_url: str | None = None


# Exams
class Exam(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    updated_at: datetime | None
    completed_at: datetime | None = None
    score: int | None = None
    member_id: str
    question_count: int
    filters: List[str] | None = Field(default=None, sa_column=Column(ARRAY(String)))
    deleted_at: datetime | None = Field(default=None)


class ExamCreate(SQLModel):
    member_id: str
    question_count: int
    tags: list[Tag] | None = None
    filters: list[str] | None = None


class AdminExamCreate(SQLModel):
    member_uuids: list[str]
    question_ids: list[str]


class ExamAnswerInput(SQLModel):
    question_id: uuid.UUID
    answer_id: uuid.UUID


class ExamUpdate(SQLModel):
    questions: list[ExamAnswerInput]
    is_complete: bool
    started_at: datetime | None = None


class Exams(SQLModel):
    data: list[Exam]
    count: int


class Exam_Question(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    position: int
    exam_id: uuid.UUID = Field(foreign_key="exam.id", ondelete="CASCADE")
    question_id: uuid.UUID = Field(foreign_key="question.id")
    question_version: int = Field(default=1)


class ExamQuestions(SQLModel):
    data: list[Exam_Question]
    count: int


class Exam_Answer(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    exam_question_id: uuid.UUID = Field(
        foreign_key="exam_question.id", ondelete="CASCADE"
    )
    answer_id: uuid.UUID = Field(foreign_key="answer_choice.id")
    started_at: datetime | None = None


class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_event"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    request_id: str | None = Field(default=None, index=True)
    actor_email: str | None = Field(default=None, index=True)
    actor_source: str = Field(default="unknown")
    action: str = Field(index=True)
    entity_type: str = Field(index=True)
    entity_id: uuid.UUID | None = Field(default=None, index=True)
    before_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    after_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    metadata_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


# Response Models
class AnswerChoiceResponse(SQLModel):
    id: uuid.UUID
    text: str
    is_correct: bool


class ExamQuestionResponse(SQLModel):
    id: uuid.UUID
    prompt: str
    media_content_type: str | None
    explanation: str | None
    position: int
    answer_choices: list[AnswerChoiceResponse]
    user_answer_id: uuid.UUID | None = None


class ExamResponse(SQLModel):
    exam_id: uuid.UUID
    member_id: str
    created_at: datetime
    started_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
    score: int | None = None
    question_count: int
    tags: list[Tag] | None = None
    filters: list[str] | None = None
    questions: list[ExamQuestionResponse]


class ExamCreateResponse(SQLModel):
    exam_id: uuid.UUID
    member_id: str
    created_at: datetime
    started_at: datetime | None = None
    question_count: int
    tags: list[Tag] | None = None
    filters: list[str] | None = None
    questions: list[ExamQuestionResponse]


class ExamBasicInfo(SQLModel):
    id: uuid.UUID
    member_id: str
    created_at: datetime
    started_at: datetime | None = None
    updated_at: datetime | None
    completed_at: datetime | None
    score: int | None
    question_count: int
    tags: list[Tag] | None = None
    filters: list[str] | None = None


class ExamListResponse(SQLModel):
    exams: list[ExamBasicInfo]
    count: int


class MessageResponse(SQLModel):
    message: str
    exam_id: uuid.UUID | None = None
    score: int | None = None
