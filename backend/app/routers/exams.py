from datetime import UTC, datetime
import uuid
import random
from fastapi import APIRouter, HTTPException
from sqlmodel import select, func

from ..db.database import SessionDep
from ..models import (
    Exam, ExamCreate, ExamUpdate, Question, Question_Tag, Answer_Choice,
    Exam_Question, Exam_Answer, ExamResponse, ExamListResponse,
    ExamCreateResponse, MessageResponse, ExamQuestionResponse,
    AnswerChoiceResponse, ExamBasicInfo, Exam_Tag, Tag,
    QuestionReadWithUserAnswer
)
from collections import defaultdict


router = APIRouter(
    prefix='/exams',
    tags=['exams']
)


@router.get('/user/{member_id}/missed-questions', response_model=list[QuestionReadWithUserAnswer])
def get_missed_questions(member_id: str, session: SessionDep):
    """
    Get all questions that were most recently answered incorrectly by the user.
    Only returns the most recent incorrect answer for each question.
    """

    # Get all incorrectly answered questions with their exam completion timestamp and answer_id
    results = session.exec(
        select(
            Question.id,
            func.max(Exam.completed_at),
            Exam_Answer.answer_id
        )
        .join(Exam_Question, Exam_Question.question_id == Question.id)
        .join(Exam, Exam.id == Exam_Question.exam_id)
        .join(Exam_Answer, Exam_Answer.exam_question_id == Exam_Question.id)
        .join(Answer_Choice, Answer_Choice.id == Exam_Answer.answer_id)
        .where(Exam.member_id == member_id)
        .where(Exam.completed_at.is_not(None))
        .where(Answer_Choice.is_correct.is_(False))
        .where(Exam.deleted_at.is_(None))
        .where(Question.deleted_at.is_(None))
        .group_by(Question.id, Exam.completed_at, Exam_Answer.answer_id)
        .order_by(Exam.completed_at.desc())
    ).all()

    if not results:
        return []

    # Get the question IDs and create a map of question_id to answer_id
    question_ids = [r[0] for r in results]
    user_answers = {r[0]: r[2] for r in results}

    # Fetch the full question details
    questions = session.exec(
        select(Question).where(Question.id.in_(question_ids))
    ).all()

    # Create a map for ordering
    question_order = {qid: idx for idx, (qid, _, _) in enumerate(results)}
    questions_sorted = sorted(questions, key=lambda q: question_order[q.id])

    # Fetch answer choices for all questions
    answer_choices = session.exec(
        select(Answer_Choice).where(
            Answer_Choice.question_id.in_(question_ids))
    ).all()
    answer_choices_by_question = defaultdict(list)
    for ac in answer_choices:
        answer_choices_by_question[ac.question_id].append(ac)

    # Fetch tags for all questions
    question_tag = session.exec(
        select(Question_Tag).where(
            Question_Tag.question_id.in_(question_ids))
    ).all()

    tag_ids = list(set(qt.tag_id for qt in question_tag))
    tags = session.exec(
        select(Tag).where(Tag.id.in_(tag_ids))
    ).all() if tag_ids else []
    tags_by_id = {tag.id: tag for tag in tags}

    tags_by_question = defaultdict(list)
    for qt in question_tag:
        if qt.tag_id in tags_by_id:
            tags_by_question[qt.question_id].append(tags_by_id[qt.tag_id])

    # Build response
    questions_data = [
        QuestionReadWithUserAnswer(
            id=q.id,
            prompt=q.prompt,
            media_storage_path=q.media_storage_path,
            media_content_type=q.media_content_type,
            explanation=q.explanation,
            answerChoices=answer_choices_by_question[q.id],
            tags=tags_by_question[q.id] or None,
            user_answer_id=user_answers.get(q.id),
            deleted_at=q.deleted_at
        )
        for q in questions_sorted
    ]

    return questions_data


@router.get('/user/{member_id}', response_model=ExamListResponse)
def read_exams_by_user(member_id: str, session: SessionDep):
    exams = session.exec(
        select(Exam)
        .where(Exam.member_id == member_id)
        .where(Exam.deleted_at.is_(None))
    ).all()

    # Fetch all exam tags in one query
    exam_ids = [exam.id for exam in exams]
    exam_tags = session.exec(
        select(Exam_Tag).where(Exam_Tag.exam_id.in_(exam_ids))
    ).all() if exam_ids else []

    # Fetch all relevant tags
    tag_ids = list(set(et.tag_id for et in exam_tags))
    tags = session.exec(
        select(Tag).where(Tag.id.in_(tag_ids))
    ).all() if tag_ids else []
    tags_by_id = {tag.id: tag for tag in tags}

    # Group tags by exam
    from collections import defaultdict
    tags_by_exam = defaultdict(list)
    for et in exam_tags:
        if et.tag_id in tags_by_id:
            tags_by_exam[et.exam_id].append(tags_by_id[et.tag_id])

    exam_list = [
        ExamBasicInfo(
            id=exam.id,
            member_id=exam.member_id,
            started_at=exam.started_at,
            updated_at=exam.updated_at,
            completed_at=exam.completed_at,
            score=exam.score,
            question_count=exam.question_count,
            tags=tags_by_exam.get(exam.id) or None,
            filters=exam.filters
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
        # Fetch the specific version of the question that was shown in the exam
        # If the question has been updated, we still show the original version
        if eq.question_version == 1:
            # This is the original version
            question = session.get(Question, eq.question_id)
        else:
            # Find the specific version by checking version and base_question_id
            # First try to find by exact ID (in case it's a later version)
            question = session.get(Question, eq.question_id)
            if question and question.version != eq.question_version:
                # The question ID doesn't match the version, search for the right version
                base_id = question.base_question_id if question.base_question_id else eq.question_id
                question = session.exec(
                    select(Question).where(
                        Question.version == eq.question_version
                    ).where(
                        (Question.id == base_id) | (
                            Question.base_question_id == base_id)
                    )
                ).first()

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
                media_storage_path=question.media_storage_path,
                media_content_type=question.media_content_type,
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

    # Fetch tags for this exam
    exam_tag_links = session.exec(
        select(Exam_Tag).where(Exam_Tag.exam_id == exam_id)
    ).all()

    tags = []
    if exam_tag_links:
        tag_ids = [et.tag_id for et in exam_tag_links]
        tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()

    return ExamResponse(
        exam_id=exam.id,
        member_id=exam.member_id,
        started_at=exam.started_at,
        updated_at=exam.updated_at,
        completed_at=exam.completed_at,
        score=exam.score,
        question_count=exam.question_count,
        tags=tags or None,
        filters=exam.filters,
        questions=questions_data
    )


@router.post('/', response_model=ExamCreateResponse)
def create_exam(*, session: SessionDep, exam_in: ExamCreate):
    # Query questions based on tags or get all questions
    if exam_in.tags and len(exam_in.tags) > 0:
        tag_ids = [tag.id for tag in exam_in.tags]
        statement = (
            select(Question)
            .join(Question_Tag)
            .where(Question_Tag.tag_id.in_(tag_ids))
            .where(Question.deleted_at.is_(None))
            .distinct()
        )
    else:
        statement = select(Question).where(Question.deleted_at.is_(None))

    questions = session.exec(statement).all()

    # Apply questions filter if specified
    if exam_in.filters:
        # Validate filter values
        valid_filters = {"used", "missed"}
        invalid_filters = set(exam_in.filters) - valid_filters
        if invalid_filters:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter values: {', '.join(invalid_filters)}. Valid values are: {', '.join(valid_filters)}."
            )

        filtered_question_ids = set(q.id for q in questions)

        # Filter to only "used" questions (questions answered in completed exams)
        if "used" in exam_in.filters:
            used_questions = session.exec(
                select(Question.id)
                .join(Exam_Question, Exam_Question.question_id == Question.id)
                .join(Exam, Exam.id == Exam_Question.exam_id)
                .join(Exam_Answer, Exam_Answer.exam_question_id == Exam_Question.id)
                .where(Exam.member_id == exam_in.member_id)
                .where(Exam.completed_at.is_not(None))
                .where(Exam.deleted_at.is_(None))
            ).all()
            filtered_question_ids &= set(used_questions)

        # Filter to only "missed" questions (incorrectly answered in completed exams)
        if "missed" in exam_in.filters:
            missed_questions = session.exec(
                select(Question.id)
                .join(Exam_Question, Exam_Question.question_id == Question.id)
                .join(Exam, Exam.id == Exam_Question.exam_id)
                .join(Exam_Answer, Exam_Answer.exam_question_id == Exam_Question.id)
                .join(Answer_Choice, Answer_Choice.id == Exam_Answer.answer_id)
                .where(Exam.member_id == exam_in.member_id)
                .where(Exam.completed_at.is_not(None))
                .where(Answer_Choice.is_correct.is_(False))
                .where(Exam.deleted_at.is_(None))
            ).all()
            filtered_question_ids &= set(missed_questions)

        # Apply the filter
        questions = [q for q in questions if q.id in filtered_question_ids]

    # Check if there are any questions available
    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No questions available to create this exam with the specified criteria"
        )

    num_questions_to_select = min(len(questions), exam_in.question_count)
    selected_questions = random.sample(questions, num_questions_to_select)

    # Create exam
    exam = Exam(
        member_id=exam_in.member_id,
        started_at=datetime.now(UTC),
        question_count=len(questions),
        filters=exam_in.filters
    )
    session.add(exam)
    session.flush()  # Get exam.id without committing

    # Create exam-tag relationships
    if exam_in.tags:
        exam_tags = [
            Exam_Tag(
                exam_id=exam.id,
                tag_id=tag.id
            )
            for tag in exam_in.tags
        ]
        session.add_all(exam_tags)

    # Create exam_question entries with version tracking
    for position, question in enumerate(selected_questions, start=1):
        exam_question = Exam_Question(
            exam_id=exam.id,
            question_id=question.id,
            question_version=question.version,
            position=position
        )
        session.add(exam_question)
    session.commit()
    session.refresh(exam)

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
                media_storage_path=question.media_storage_path,
                media_content_type=question.media_content_type,
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

    # Fetch tags for response
    exam_tag_links = session.exec(
        select(Exam_Tag).where(Exam_Tag.exam_id == exam.id)
    ).all()

    tags = []
    if exam_tag_links:
        tag_ids = [et.tag_id for et in exam_tag_links]
        tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()

    return ExamCreateResponse(
        exam_id=exam.id,
        member_id=exam.member_id,
        started_at=exam.started_at,
        question_count=exam.question_count,
        tags=tags or None,
        filters=exam.filters,
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
