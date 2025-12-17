from datetime import datetime
import uuid
from sqlmodel import Field, SQLModel


# Questions
class TagBase(SQLModel):
    name: str


class Tag(TagBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4,
                          primary_key=True, index=True)


class TagCreate(TagBase):
    pass


class TagUpdate(TagBase):
    pass


class Tags(SQLModel):
    data: list[Tag]
    count: int


class Question_Tags(SQLModel, table=True):
    question_id: uuid.UUID = Field(
        foreign_key='question.id', primary_key=True, ondelete='CASCADE')
    tag_id: uuid.UUID = Field(foreign_key='tag.id', primary_key=True)


class QuestionBase(SQLModel):
    prompt: str
    media_url: str | None = Field(default=None)
    explanation: str | None = Field(default=None)


class Question(QuestionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4,
                          primary_key=True, index=True)
    deleted_at: datetime | None = Field(default=None)


class AnswerChoiceBase(SQLModel):
    text: str
    is_correct: bool


class Answer_Choice(AnswerChoiceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4,
                          primary_key=True, index=True)
    question_id: uuid.UUID = Field(
        foreign_key='question.id', ondelete='CASCADE')


class QuestionCreate(QuestionBase):
    tags: list[TagBase] | None = Field(default=None)
    answerChoices: list[AnswerChoiceBase]


class QuestionRead(QuestionBase):
    id: uuid.UUID
    tags: list[TagBase] | None = Field(default=None)
    answerChoices: list[AnswerChoiceBase]
    deleted_at: datetime | None = None


class QuestionUpdate(QuestionBase):
    prompt: str | None
    tags: list[TagBase] | None
    answerChoices: list[AnswerChoiceBase] | None


class Questions(SQLModel):
    data: list[QuestionRead]
    count: int


# Exams
class Exam(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4,
                          primary_key=True, index=True)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    score: int
    member_id: str


class ExamCreate(SQLModel):
    member_id: str
    question_count: int
    tags: list[Tag] | None


class ExamUpdate(SQLModel):
    pass


class Exams(SQLModel):
    data: list[Exam]
    count: int


class Exam_Question(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4,
                          primary_key=True, index=True)
    position: int
    exam_id: uuid.UUID = Field(foreign_key='exam.id')
    question_id: uuid.UUID = Field(foreign_key='question.id')


class ExamQuestions(SQLModel):
    data: list[Exam_Question]
    count: int


class Exam_Answer(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4,
                          primary_key=True, index=True)
    exam_question_id: uuid.UUID = Field(foreign_key='exam_question.id')
    answer_id: uuid.UUID = Field(foreign_key='answer_choice.id')
