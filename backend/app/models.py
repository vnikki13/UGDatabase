from datetime import datetime
from sqlmodel import Field, SQLModel


class Member(SQLModel, table=True):
    id: int = Field(primary_key=True, index=True)
    email: str = Field(index=True)
    name: str


# Questions
class Tag(SQLModel, table=True):
    id: int | None = Field(default=True, primary_key=True, index=True)
    name: str


class Question_Categories(SQLModel, table=True):
    question_id: int | None = Field(
        default=None, foreign_key='question.id', primary_key=True)
    category_id: int | None = Field(
        default=None, foreign_key='category.id', primary_key=True)


class Category(SQLModel, table=True):
    id: int | None = Field(default=True, primary_key=True, index=True)
    name: str


class Question(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    prompt: str
    media_url: str
    explanation: str
    tag_id: int = Field(default=None, foreign_key='tag.id')


class Answer_Choice(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, index=True)
    text: str
    is_correct: bool
    question_id: int = Field(default=None, foreign_key='question.id')


# Exams
class Exam(SQLModel, table=True):
    id: int | None = Field(default=True, primary_key=True, index=True)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    score: int
    member_id: int | None = Field(default=None, foreign_key='member.id')


class Exam_Question(SQLModel, table=True):
    id: int | None = Field(default=True, primary_key=True, index=True)
    position: int
    exam_id: int = Field(default=None, foreign_key='exam.id')
    question_id: int = Field(default=None, foreign_key='question.id')


class Exam_Answer(SQLModel, table=True):
    id: int | None = Field(default=True, primary_key=True, index=True)
    exam_question_id: int = Field(default=None, foreign_key='exam_question.id')
    answer_id: int = Field(default=None, foreign_key='answer_choice.id')
