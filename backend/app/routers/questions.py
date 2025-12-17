import uuid
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..db.database import SessionDep
from ..models import Question, QuestionCreate


router = APIRouter(
    prefix='/questions',
    tags=['questions']
)


@router.get('/')
def read_questions(session: SessionDep):
    questions = session.exec(select(Question)).all()
    return questions


@router.get('/{question_id}')
def read_question_by_id(question_id: uuid.UUID, session: SessionDep):
    question = session.get(Question, question_id)
    return question


@router.post('/', response_model=Question)
def create_question(*, session: SessionDep, question: QuestionCreate):
    session.add(question)
    session.commit()
    return question

@router.put('/{question_id}', response_model=Question)
def update_question(*, session: SessionDep, question_id: int, question_in: Question):
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    update_dict = question_in.model_dump(exclude_unset=True)
    question.sqlmodel_update(update_dict)
    session.add(question)
    session.commit()
    session.refresh(question)
    return question


@router.delete('/{question_id}')
def delete_question(session: SessionDep, question_id: uuid.UUID):
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    session.delete(question)
    session.commit()
    return {'message': 'Question deleted successfully'}
