from datetime import UTC, datetime
import uuid
import random
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..db.database import SessionDep
from ..models import (
    Exam, ExamCreate, ExamUpdate, Question, Question_Tags, Answer_Choice,
    Exam_Question, Exam_Answer, ExamResponse, ExamListResponse,
    ExamCreateResponse, MessageResponse, ExamQuestionResponse,
    AnswerChoiceResponse, ExamBasicInfo
)


router = APIRouter(
    prefix='/exams',
    tags=['exams']
)


@router.get('/user/{member_id}', response_model=ExamListResponse)
def read_exams_by_user(member_id: str, session: SessionDep):
    exams = session.exec(
        select(Exam)
        .where(Exam.member_id == member_id)
        .where(Exam.deleted_at.is_(None))
    ).all()

    exam_list = [
        ExamBasicInfo(
            id=exam.id,
            member_id=exam.member_id,
            started_at=exam.started_at,
            updated_at=exam.updated_at,
            completed_at=exam.completed_at,
            score=exam.score
        ) for exam in exams
    ]

    return ExamListResponse(exams=exam_list, count=len(exam_list))


@router.get('/{exam_id}', response_model=ExamResponse)
def read_exam_by_id(exam_id: uuid.UUID, session: SessionDep):
    exam = session.get(Exam, exam_id)
    if not exam or exam.deleted_at:
        raise HTTPException(status_code=404, detail="Exam not found")

    exam_questions = session.exec(
        select(Exam_Question)
        .where(Exam_Question.exam_id == exam_id)
        .order_by(Exam_Question.position)
    ).all()

    questions_data = []
    for eq in exam_questions:
        question = session.get(Question, eq.question_id)
        if not question:
            continue

        answer_choices = session.exec(
            select(Answer_Choice).where(
                Answer_Choice.question_id == question.id)
        ).all()

        user_answer = session.exec(
            select(Exam_Answer).where(Exam_Answer.exam_question_id == eq.id)
        ).first()

        questions_data.append(
            ExamQuestionResponse(
                id=question.id,
                prompt=question.prompt,
                media_url=question.media_url,
                explanation=question.explanation,
                position=eq.position,
                answer_choices=[
                    AnswerChoiceResponse(
                        id=ac.id,
                        text=ac.text,
                        is_correct=ac.is_correct
                    ) for ac in answer_choices
                ],
                user_answer_id=user_answer.answer_id if user_answer else None
            )
        )

    return ExamResponse(
        exam_id=exam.id,
        member_id=exam.member_id,
        started_at=exam.started_at,
        updated_at=exam.updated_at,
        completed_at=exam.completed_at,
        score=exam.score,
        questions=questions_data
    )


@router.post('/', response_model=ExamCreateResponse)
def create_exam(*, session: SessionDep, exam_in: ExamCreate):
    # Query questions based on tags or get all questions
    if exam_in.tags and len(exam_in.tags) > 0:
        tag_ids = [tag.id for tag in exam_in.tags]
        statement = (
            select(Question)
            .join(Question_Tags)
            .where(Question_Tags.tag_id.in_(tag_ids))
            .where(Question.deleted_at.is_(None))
            .distinct()
        )
    else:
        statement = select(Question).where(Question.deleted_at.is_(None))

    questions = session.exec(statement).all()
    num_questions_to_select = min(len(questions), exam_in.question_count)
    selected_questions = random.sample(questions, num_questions_to_select)

    # Create exam
    exam = Exam(member_id=exam_in.member_id, started_at=datetime.now(UTC))
    session.add(exam)
    session.commit()
    session.refresh(exam)

    # Create exam_question entries
    for position, question in enumerate(selected_questions, start=1):
        exam_question = Exam_Question(
            exam_id=exam.id,
            question_id=question.id,
            position=position
        )
        session.add(exam_question)
    session.commit()

    # Build response with questions and answer choices
    questions_data = []
    for position, question in enumerate(selected_questions, start=1):
        answer_choices = session.exec(
            select(Answer_Choice).where(
                Answer_Choice.question_id == question.id)
        ).all()

        questions_data.append(
            ExamQuestionResponse(
                id=question.id,
                prompt=question.prompt,
                media_url=question.media_url,
                explanation=question.explanation,
                position=position,
                answer_choices=[
                    AnswerChoiceResponse(
                        id=ac.id,
                        text=ac.text,
                        is_correct=ac.is_correct
                    ) for ac in answer_choices
                ]
            )
        )

    return ExamCreateResponse(
        exam_id=exam.id,
        member_id=exam.member_id,
        started_at=exam.started_at,
        questions=questions_data
    )


@router.put('/{exam_id}')
def update_exam(*, session: SessionDep, exam_id: uuid.UUID, exam_in: ExamUpdate):
    # Verify exam exists
    exam = session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Get all exam questions for this exam
    exam_questions = session.exec(
        select(Exam_Question).where(Exam_Question.exam_id == exam_id)
    ).all()

    exam_question_map = {eq.question_id: eq.id for eq in exam_questions}

    # Get already answered question IDs
    existing_answers = session.exec(
        select(Exam_Answer.exam_question_id)
        .join(Exam_Question)
        .where(Exam_Question.exam_id == exam_id)
    ).all()

    answered_exam_question_ids = set(existing_answers)

    # Save only new answers (skip questions that already have answers)
    for answer_input in exam_in.questions:
        exam_question_id = exam_question_map.get(answer_input.question_id)
        if not exam_question_id:
            raise HTTPException(
                status_code=400,
                detail=f"Question {answer_input.question_id} not found"
            )

        if exam_question_id not in answered_exam_question_ids:
            session.add(Exam_Answer(
                exam_question_id=exam_question_id,
                answer_id=answer_input.answer_id
            ))

    exam.updated_at = datetime.now(UTC)

    # If complete, calculate score
    if exam_in.is_complete:
        result = session.exec(
            select(Exam_Question, Exam_Answer, Answer_Choice)
            .join(Exam_Answer, Exam_Answer.exam_question_id == Exam_Question.id, isouter=True)
            .join(Answer_Choice, Answer_Choice.id == Exam_Answer.answer_id, isouter=True)
            .where(Exam_Question.exam_id == exam_id)
        ).all()

        total_questions = len(result)
        correct_answers = sum(1 for _, _, ac in result if ac and ac.is_correct)

        exam.score = int((correct_answers / total_questions * 100)
                         ) if total_questions > 0 else 0
        exam.completed_at = datetime.now(UTC)

    session.add(exam)
    session.commit()

    return MessageResponse(message="Exam answers saved successfully", exam_id=exam_id)


@router.delete('/{exam_id}', response_model=MessageResponse)
def soft_delete_exam(exam_id: uuid.UUID, session: SessionDep):
    exam = session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if exam.deleted_at:
        raise HTTPException(status_code=400, detail="Exam already deleted")

    exam.deleted_at = datetime.now(UTC)
    session.add(exam)
    session.commit()

    return MessageResponse(message="Exam soft deleted successfully")


@router.delete('/user/{member_id}/all', response_model=MessageResponse)
def soft_delete_all_user_exams(member_id: str, session: SessionDep):
    exams = session.exec(
        select(Exam)
        .where(Exam.member_id == member_id)
        .where(Exam.deleted_at.is_(None))
    ).all()

    if not exams:
        return MessageResponse(message="No exams found for this user")

    for exam in exams:
        exam.deleted_at = datetime.now(UTC)
        session.add(exam)

    session.commit()
    return MessageResponse(message=f"Soft deleted {len(exams)} exams successfully")


@router.delete('/{exam_id}/hard', response_model=MessageResponse)
def hard_delete_exam(exam_id: uuid.UUID, session: SessionDep):
    exam = session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    session.delete(exam)
    session.commit()

    return MessageResponse(message="Exam permanently deleted")


@router.delete('/user/{member_id}/all/hard', response_model=MessageResponse)
def hard_delete_all_user_exams(member_id: str, session: SessionDep):
    exams = session.exec(
        select(Exam).where(Exam.member_id == member_id)
    ).all()

    if not exams:
        return MessageResponse(message="No exams found for this user")

    for exam in exams:
        session.delete(exam)

    session.commit()
    return MessageResponse(message=f"Permanently deleted {len(exams)} exams")
