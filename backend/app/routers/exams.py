from datetime import UTC, datetime
import uuid
import random
from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select, func

from app.audit import get_audit_context, record_audit_event
from app.db.database import SessionDep
from app.models import (
    AdminExamCreate,
    Exam,
    ExamCreate,
    ExamUpdate,
    Question,
    Question_Tag,
    Answer_Choice,
    Exam_Question,
    Exam_Answer,
    ExamResponse,
    ExamListResponse,
    ExamCreateResponse,
    MessageResponse,
    ExamQuestionResponse,
    AnswerChoiceResponse,
    ExamBasicInfo,
    Exam_Tag,
    Tag,
    QuestionReadWithUserAnswer,
)
from typing import List
from collections import defaultdict


router = APIRouter(prefix="/exams", tags=["exams"])


def _question_lineage_id(question: Question) -> uuid.UUID:
    return question.base_question_id or question.id


def _serialize_exam(exam: Exam | None):
    if exam is None:
        return None

    return {
        "id": str(exam.id),
        "member_id": exam.member_id,
        "created_at": exam.created_at.isoformat() if exam.created_at else None,
        "started_at": exam.started_at.isoformat() if exam.started_at else None,
        "updated_at": exam.updated_at.isoformat() if exam.updated_at else None,
        "completed_at": exam.completed_at.isoformat() if exam.completed_at else None,
        "score": exam.score,
        "question_count": exam.question_count,
        "filters": exam.filters,
        "deleted_at": exam.deleted_at.isoformat() if exam.deleted_at else None,
    }


@router.get(
    "/user/{member_id}/missed-questions",
    response_model=list[QuestionReadWithUserAnswer],
)
def get_missed_questions(member_id: str, session: SessionDep):
    """
    Get all questions that were most recently answered incorrectly by the user.
    Only returns the most recent incorrect answer for each question.
    """

    # Get all incorrectly answered questions with their exam completion timestamp and answer_id
    results = session.exec(
        select(Question.id, func.max(Exam.completed_at), Exam_Answer.answer_id)
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
        select(Answer_Choice).where(Answer_Choice.question_id.in_(question_ids))
    ).all()
    answer_choices_by_question = defaultdict(list)
    for ac in answer_choices:
        answer_choices_by_question[ac.question_id].append(ac)

    # Fetch tags for all questions
    question_tag = session.exec(
        select(Question_Tag).where(Question_Tag.question_id.in_(question_ids))
    ).all()

    tag_ids = list(set(qt.tag_id for qt in question_tag))
    tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all() if tag_ids else []
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
            media_content_type=q.media_content_type,
            explanation=q.explanation,
            answerChoices=answer_choices_by_question[q.id],
            tags=tags_by_question[q.id] or None,
            user_answer_id=user_answers.get(q.id),
            deleted_at=q.deleted_at,
        )
        for q in questions_sorted
    ]

    return questions_data


@router.get("/user/{member_id}", response_model=ExamListResponse)
def read_exams_by_user(member_id: str, session: SessionDep):
    exams = session.exec(
        select(Exam).where(Exam.member_id == member_id).where(Exam.deleted_at.is_(None))
    ).all()

    # Fetch all exam tags in one query
    exam_ids = [exam.id for exam in exams]
    exam_tags = (
        session.exec(select(Exam_Tag).where(Exam_Tag.exam_id.in_(exam_ids))).all()
        if exam_ids
        else []
    )

    # Fetch all relevant tags
    tag_ids = list(set(et.tag_id for et in exam_tags))
    tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all() if tag_ids else []
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
            created_at=exam.created_at,
            started_at=exam.started_at,
            updated_at=exam.updated_at,
            completed_at=exam.completed_at,
            score=exam.score,
            question_count=exam.question_count,
            tags=tags_by_exam.get(exam.id) or None,
            filters=exam.filters,
        )
        for exam in exams
    ]

    return ExamListResponse(exams=exam_list, count=len(exam_list))


@router.get("/admin", response_model=ExamListResponse)
def read_admin_exams(session: SessionDep):
    exams = session.exec(
        select(Exam)
        .where(Exam.deleted_at.is_(None))
        .where(Exam.filters.is_not(None))
        .where(Exam.filters.any("admin"))
    ).all()

    exam_ids = [exam.id for exam in exams]
    exam_tags = (
        session.exec(select(Exam_Tag).where(Exam_Tag.exam_id.in_(exam_ids))).all()
        if exam_ids
        else []
    )

    tag_ids = list(set(et.tag_id for et in exam_tags))
    tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all() if tag_ids else []
    tags_by_id = {tag.id: tag for tag in tags}

    tags_by_exam = defaultdict(list)
    for et in exam_tags:
        if et.tag_id in tags_by_id:
            tags_by_exam[et.exam_id].append(tags_by_id[et.tag_id])

    exam_list = [
        ExamBasicInfo(
            id=exam.id,
            member_id=exam.member_id,
            created_at=exam.created_at,
            started_at=exam.started_at,
            updated_at=exam.updated_at,
            completed_at=exam.completed_at,
            score=exam.score,
            question_count=exam.question_count,
            tags=tags_by_exam.get(exam.id) or None,
            filters=exam.filters,
        )
        for exam in exams
    ]

    return ExamListResponse(exams=exam_list, count=len(exam_list))


@router.get("/{exam_id}", response_model=ExamResponse)
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
                base_id = (
                    question.base_question_id
                    if question.base_question_id
                    else eq.question_id
                )
                question = session.exec(
                    select(Question)
                    .where(Question.version == eq.question_version)
                    .where(
                        (Question.id == base_id)
                        | (Question.base_question_id == base_id)
                    )
                ).first()

        if not question:
            continue

        answer_choices = session.exec(
            select(Answer_Choice).where(Answer_Choice.question_id == question.id)
        ).all()

        user_answer = session.exec(
            select(Exam_Answer).where(Exam_Answer.exam_question_id == eq.id)
        ).first()

        questions_data.append(
            ExamQuestionResponse(
                id=question.id,
                prompt=question.prompt,
                media_content_type=question.media_content_type,
                explanation=question.explanation,
                position=eq.position,
                answer_choices=[
                    AnswerChoiceResponse(
                        id=ac.id, text=ac.text, is_correct=ac.is_correct
                    )
                    for ac in answer_choices
                ],
                user_answer_id=user_answer.answer_id if user_answer else None,
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
        created_at=exam.created_at,
        started_at=exam.started_at,
        updated_at=exam.updated_at,
        completed_at=exam.completed_at,
        score=exam.score,
        question_count=exam.question_count,
        tags=tags or None,
        filters=exam.filters,
        questions=questions_data,
    )


@router.post("/", response_model=ExamCreateResponse)
def create_exam(*, session: SessionDep, exam_in: ExamCreate):
    # Query questions based on tags or get all questions
    if exam_in.tags and len(exam_in.tags) > 0:
        tag_ids = [tag.id for tag in exam_in.tags]
        statement = (
            select(Question)
            .join(Question_Tag)
            .where(Question_Tag.tag_id.in_(tag_ids))
            .distinct()
        )
    else:
        statement = select(Question)

    questions = session.exec(statement).all()

    # Keep only the latest version per question lineage, then include only
    # lineages whose latest version is not soft-deleted.
    latest_by_lineage: dict[uuid.UUID, Question] = {}
    for question in questions:
        lineage_id = _question_lineage_id(question)
        current = latest_by_lineage.get(lineage_id)
        if current is None or question.version > current.version:
            latest_by_lineage[lineage_id] = question
    questions = [
        question
        for question in latest_by_lineage.values()
        if question.deleted_at is None
    ]

    # Apply questions filter - if no filters specified, apply all filters
    filters_to_apply = (
        exam_in.filters if exam_in.filters else ["missed", "correct", "unanswered"]
    )

    if filters_to_apply:
        # Validate filter values
        valid_filters = {"missed", "correct", "unanswered"}
        invalid_filters = set(filters_to_apply) - valid_filters
        if invalid_filters:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter values: {', '.join(invalid_filters)}. Valid values are: {', '.join(valid_filters)}.",
            )

        # Start with empty set and union all filter results
        filtered_lineage_ids = set()
        available_lineage_ids = {_question_lineage_id(q) for q in questions}

        # Filter to only "missed" questions (incorrectly answered in completed exams)
        if "missed" in filters_to_apply:
            missed_lineages = session.exec(
                select(func.coalesce(Question.base_question_id, Question.id))
                .join(Exam_Question, Exam_Question.question_id == Question.id)
                .join(Exam, Exam.id == Exam_Question.exam_id)
                .join(Exam_Answer, Exam_Answer.exam_question_id == Exam_Question.id)
                .join(Answer_Choice, Answer_Choice.id == Exam_Answer.answer_id)
                .where(Exam.member_id == exam_in.member_id)
                .where(Exam.completed_at.is_not(None))
                .where(Answer_Choice.is_correct.is_(False))
                .where(Exam.deleted_at.is_(None))
            ).all()
            filtered_lineage_ids |= set(missed_lineages)

        # Filter to only "correct" questions (correctly answered in completed exams)
        if "correct" in filters_to_apply:
            correct_lineages = session.exec(
                select(func.coalesce(Question.base_question_id, Question.id))
                .join(Exam_Question, Exam_Question.question_id == Question.id)
                .join(Exam, Exam.id == Exam_Question.exam_id)
                .join(Exam_Answer, Exam_Answer.exam_question_id == Exam_Question.id)
                .join(Answer_Choice, Answer_Choice.id == Exam_Answer.answer_id)
                .where(Exam.member_id == exam_in.member_id)
                .where(Exam.completed_at.is_not(None))
                .where(Answer_Choice.is_correct.is_(True))
                .where(Exam.deleted_at.is_(None))
            ).all()
            filtered_lineage_ids |= set(correct_lineages)

        # Filter to only "unanswered" questions (never been in an exam)
        if "unanswered" in filters_to_apply:
            used_lineages = session.exec(
                select(func.coalesce(Question.base_question_id, Question.id))
                .join(Exam_Question, Exam_Question.question_id == Question.id)
                .join(Exam, Exam.id == Exam_Question.exam_id)
                .where(Exam.member_id == exam_in.member_id)
                .where(Exam.deleted_at.is_(None))
            ).all()
            used_set = set(used_lineages)
            # Add questions that have never been in an exam
            unanswered = available_lineage_ids - used_set
            filtered_lineage_ids |= unanswered

        # Apply the filter - only keep questions that match at least one filter
        questions = [
            q for q in questions if _question_lineage_id(q) in filtered_lineage_ids
        ]

    # Check if there are any questions available
    if not questions:
        raise HTTPException(
            status_code=404,
            detail="No questions available to create this exam with the specified criteria",
        )

    num_questions_to_select = min(len(questions), exam_in.question_count)
    selected_questions = random.sample(questions, num_questions_to_select)

    # Create exam
    exam = Exam(
        member_id=exam_in.member_id,
        created_at=datetime.now(UTC),
        started_at=datetime.now(UTC),
        question_count=len(questions),
        filters=exam_in.filters,
    )
    session.add(exam)
    session.flush()  # Get exam.id without committing

    # Create exam-tag relationships
    if exam_in.tags:
        exam_tags = [Exam_Tag(exam_id=exam.id, tag_id=tag.id) for tag in exam_in.tags]
        session.add_all(exam_tags)

    # Create exam_question entries with version tracking
    selected_question_ids = []
    for position, question in enumerate(selected_questions, start=1):
        exam_question = Exam_Question(
            exam_id=exam.id,
            question_id=question.id,
            question_version=question.version,
            position=position,
        )
        session.add(exam_question)
        selected_question_ids.append(str(question.id))

    session.commit()
    session.refresh(exam)

    # Build response with questions and answer choices
    questions_data = []
    for position, question in enumerate(selected_questions, start=1):
        answer_choices = session.exec(
            select(Answer_Choice).where(Answer_Choice.question_id == question.id)
        ).all()

        questions_data.append(
            ExamQuestionResponse(
                id=question.id,
                prompt=question.prompt,
                media_content_type=question.media_content_type,
                explanation=question.explanation,
                position=position,
                answer_choices=[
                    AnswerChoiceResponse(
                        id=ac.id, text=ac.text, is_correct=ac.is_correct
                    )
                    for ac in answer_choices
                ],
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
        created_at=exam.created_at,
        started_at=exam.started_at,
        question_count=exam.question_count,
        tags=tags or None,
        filters=exam.filters,
        questions=questions_data,
    )


@router.post("/admin", response_model=List[ExamCreateResponse])
def create_admin_exams(
    *, session: SessionDep, request: Request, exam_in: AdminExamCreate
):
    """
    Create an exam for each member in 'members' with the provided 'questionIds'.
    Adds 'admin' filter and leaves started_at, completed_at, score, deleted_at empty.
    """
    members = exam_in.member_uuids
    question_ids = exam_in.question_ids
    if not members or not question_ids:
        raise HTTPException(
            status_code=400,
            detail="Both 'member_uuids' and 'question_ids' are required.",
        )

    parsed_question_ids: list[uuid.UUID] = []
    for question_id in question_ids:
        try:
            parsed_question_ids.append(uuid.UUID(question_id))
        except ValueError as err:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid question UUID: {question_id}",
            ) from err

    unique_question_ids = list(dict.fromkeys(parsed_question_ids))
    existing_questions = session.exec(
        select(Question).where(Question.id.in_(unique_question_ids))
    ).all()
    questions_by_id = {question.id: question for question in existing_questions}

    missing_question_ids = [
        str(question_id)
        for question_id in unique_question_ids
        if question_id not in questions_by_id
    ]
    if missing_question_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Questions do not exist: {', '.join(missing_question_ids)}",
        )

    deleted_question_ids = [
        str(question.id)
        for question in existing_questions
        if question.deleted_at is not None
    ]
    if deleted_question_ids:
        raise HTTPException(
            status_code=400,
            detail=(
                "Deleted questions cannot be used in exams: "
                f"{', '.join(deleted_question_ids)}"
            ),
        )

    question_ids = parsed_question_ids

    responses = []
    context = get_audit_context(request)
    for member in members:
        exam = Exam(
            member_id=member,
            created_at=datetime.now(UTC),
            started_at=None,
            updated_at=None,
            completed_at=None,
            score=None,
            question_count=len(question_ids),
            filters=["admin"],
            deleted_at=None,
        )
        session.add(exam)
        session.flush()

        # Create Exam_Question entries
        questions_data = []
        for position, qid in enumerate(question_ids, start=1):
            eq = Exam_Question(
                exam_id=exam.id, question_id=qid, question_version=1, position=position
            )
            session.add(eq)
            # Optionally, fetch question details for response
            question = session.get(Question, qid)
            if question:
                answer_choices = session.exec(
                    select(Answer_Choice).where(Answer_Choice.question_id == qid)
                ).all()
                questions_data.append(
                    ExamQuestionResponse(
                        id=question.id,
                        prompt=question.prompt,
                        media_content_type=question.media_content_type,
                        explanation=question.explanation,
                        position=position,
                        answer_choices=[
                            AnswerChoiceResponse(
                                id=ac.id, text=ac.text, is_correct=ac.is_correct
                            )
                            for ac in answer_choices
                        ],
                    )
                )

        record_audit_event(
            session,
            context=context,
            action="exam.admin_create",
            entity_type="exam",
            entity_id=exam.id,
            after=_serialize_exam(exam),
            metadata={
                "member_uuid": member,
                "question_ids": [str(qid) for qid in question_ids],
            },
        )

        session.commit()
        session.refresh(exam)

        # Fetch tags for response
        exam_tag_links = session.exec(
            select(Exam_Tag).where(Exam_Tag.exam_id == exam.id)
        ).all()

        tags = []
        if exam_tag_links:
            tag_ids = [et.tag_id for et in exam_tag_links]
            tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()

        responses.append(
            ExamCreateResponse(
                exam_id=exam.id,
                member_id=exam.member_id,
                created_at=exam.created_at,
                started_at=exam.started_at,
                question_count=exam.question_count,
                tags=tags or None,
                filters=exam.filters,
                questions=questions_data,
            )
        )
    return responses


@router.put("/{exam_id}")
def update_exam(*, session: SessionDep, exam_id: uuid.UUID, exam_in: ExamUpdate):
    # Verify exam exists
    exam = session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Require a start timestamp on the first update of admin-created exams.
    if exam.started_at is None:
        if exam_in.started_at is None:
            raise HTTPException(
                status_code=400,
                detail="started_at is required for the first exam update",
            )
        exam.started_at = exam_in.started_at

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
                status_code=400, detail=f"Question {answer_input.question_id} not found"
            )

        if exam_question_id not in answered_exam_question_ids:
            session.add(
                Exam_Answer(
                    exam_question_id=exam_question_id, answer_id=answer_input.answer_id
                )
            )

    exam.updated_at = datetime.now(UTC)

    # If complete, calculate score
    if exam_in.is_complete:
        result = session.exec(
            select(Exam_Question, Exam_Answer, Answer_Choice)
            .join(
                Exam_Answer,
                Exam_Answer.exam_question_id == Exam_Question.id,
                isouter=True,
            )
            .join(
                Answer_Choice, Answer_Choice.id == Exam_Answer.answer_id, isouter=True
            )
            .where(Exam_Question.exam_id == exam_id)
        ).all()

        total_questions = len(result)
        correct_answers = sum(1 for _, _, ac in result if ac and ac.is_correct)

        exam.score = (
            int((correct_answers / total_questions * 100)) if total_questions > 0 else 0
        )
        exam.completed_at = datetime.now(UTC)

    session.add(exam)
    session.commit()

    return MessageResponse(
        message="Exam answers saved successfully",
        exam_id=exam_id,
        score=exam.score if exam_in.is_complete else None,
    )


@router.delete("/{exam_id}", response_model=MessageResponse)
def soft_delete_exam(exam_id: uuid.UUID, session: SessionDep, request: Request):
    exam = session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if exam.deleted_at:
        raise HTTPException(status_code=400, detail="Exam already deleted")

    before_snapshot = _serialize_exam(exam)
    exam.deleted_at = datetime.now(UTC)
    session.add(exam)
    context = get_audit_context(request)
    record_audit_event(
        session,
        context=context,
        action="exam.delete",
        entity_type="exam",
        entity_id=exam.id,
        before=before_snapshot,
        after=_serialize_exam(exam),
        metadata={"delete_type": "soft"},
    )
    session.commit()

    return MessageResponse(message="Exam soft deleted successfully")


@router.delete("/user/{member_id}/all", response_model=MessageResponse)
def soft_delete_all_user_exams(member_id: str, session: SessionDep, request: Request):
    exams = session.exec(
        select(Exam).where(Exam.member_id == member_id).where(Exam.deleted_at.is_(None))
    ).all()

    if not exams:
        return MessageResponse(message="No exams found for this user")

    context = get_audit_context(request)
    for exam in exams:
        before_snapshot = _serialize_exam(exam)
        exam.deleted_at = datetime.now(UTC)
        session.add(exam)
        record_audit_event(
            session,
            context=context,
            action="exam.delete",
            entity_type="exam",
            entity_id=exam.id,
            before=before_snapshot,
            after=_serialize_exam(exam),
            metadata={"delete_type": "soft", "bulk": True, "member_id": member_id},
        )

    session.commit()
    return MessageResponse(message=f"Soft deleted {len(exams)} exams successfully")


@router.delete("/{exam_id}/hard", response_model=MessageResponse)
def hard_delete_exam(exam_id: uuid.UUID, session: SessionDep, request: Request):
    exam = session.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    before_snapshot = _serialize_exam(exam)
    session.delete(exam)
    context = get_audit_context(request)
    record_audit_event(
        session,
        context=context,
        action="exam.delete",
        entity_type="exam",
        entity_id=exam_id,
        before=before_snapshot,
        after=None,
        metadata={"delete_type": "hard"},
    )
    session.commit()

    return MessageResponse(message="Exam permanently deleted")


@router.delete("/user/{member_id}/all/hard", response_model=MessageResponse)
def hard_delete_all_user_exams(member_id: str, session: SessionDep, request: Request):
    exams = session.exec(select(Exam).where(Exam.member_id == member_id)).all()

    if not exams:
        return MessageResponse(message="No exams found for this user")

    context = get_audit_context(request)
    for exam in exams:
        before_snapshot = _serialize_exam(exam)
        session.delete(exam)
        record_audit_event(
            session,
            context=context,
            action="exam.delete",
            entity_type="exam",
            entity_id=exam.id,
            before=before_snapshot,
            after=None,
            metadata={"delete_type": "hard", "bulk": True, "member_id": member_id},
        )

    session.commit()
    return MessageResponse(message=f"Permanently deleted {len(exams)} exams")
