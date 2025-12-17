import uuid
from collections import defaultdict
from datetime import UTC, datetime
from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from ..db.database import SessionDep
from app.models import Answer_Choice, Question, QuestionCreate, QuestionRead, QuestionUpdate, Questions, Tag, Question_Tags


router = APIRouter(
    prefix='/questions',
    tags=['questions']
)


@router.get('/')
def read_questions(session: SessionDep):
    count = session.exec(
        select(func.count()).select_from(Question).where(
            Question.deleted_at.is_(None))
    ).one()
    questions = session.exec(
        select(Question).where(Question.deleted_at.is_(None))
    ).all()

    if not questions:
        return Questions(data=[], count=count)

    # Fetch and group all answer choices
    answer_choices = session.exec(select(Answer_Choice)).all()
    answer_choices_by_question = defaultdict(list)
    for ac in answer_choices:
        answer_choices_by_question[ac.question_id].append(ac)

    # Fetch and group all tags
    question_tags = session.exec(select(Question_Tags)).all()
    tags = session.exec(select(Tag)).all()
    tags_by_id = {tag.id: tag for tag in tags}

    tags_by_question = defaultdict(list)
    for qt in question_tags:
        if qt.tag_id in tags_by_id:
            tags_by_question[qt.question_id].append(tags_by_id[qt.tag_id])

    # Build response objects
    questions_data = [
        QuestionRead(
            id=q.id,
            prompt=q.prompt,
            media_url=q.media_url,
            explanation=q.explanation,
            answerChoices=answer_choices_by_question[q.id],
            tags=tags_by_question[q.id] or None,
            deleted_at=q.deleted_at
        )
        for q in questions
    ]

    return Questions(data=questions_data, count=count)


@router.get('/{question_id}', response_model=QuestionRead)
def read_question_by_id(question_id: uuid.UUID, session: SessionDep):
    question = session.get(Question, question_id)
    if not question or question.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Question not found")

    # Fetch answer choices for this question
    answer_choices = session.exec(
        select(Answer_Choice).where(Answer_Choice.question_id == question_id)
    ).all()

    # Fetch tags for this question
    question_tags = session.exec(
        select(Question_Tags).where(Question_Tags.question_id == question_id)
    ).all()

    tags = []
    if question_tags:
        tag_ids = [qt.tag_id for qt in question_tags]
        tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()

    return QuestionRead(
        id=question.id,
        prompt=question.prompt,
        media_url=question.media_url,
        explanation=question.explanation,
        answerChoices=answer_choices,
        tags=tags or None,
        deleted_at=question.deleted_at
    )


@router.post('/', response_model=QuestionRead)
def create_question(*, session: SessionDep, question_in: QuestionCreate):
    question_create = QuestionCreate.model_validate(question_in)

    # Validate and fetch all tags in one query
    tags_dict = {}
    if question_create.tags:
        tag_names = [tag_data.name for tag_data in question_create.tags]
        existing_tags = session.exec(
            select(Tag).where(Tag.name.in_(tag_names))
        ).all()
        tags_dict = {tag.name: tag for tag in existing_tags}

        # Check if any tags are missing
        missing_tags = set(tag_names) - set(tags_dict.keys())
        if missing_tags:
            raise HTTPException(
                status_code=400,
                detail=f"Tags do not exist: {', '.join(missing_tags)}"
            )

    # Create question
    question = Question.model_validate(question_create)
    session.add(question)
    session.flush()  # Get question.id without committing

    # Batch create answer choices
    answer_choices = [
        Answer_Choice(
            text=ac.text,
            is_correct=ac.is_correct,
            question_id=question.id
        )
        for ac in question_create.answerChoices
    ]
    session.add_all(answer_choices)

    # Batch create question-tag relationships
    if question_create.tags:
        question_tags = [
            Question_Tags(
                question_id=question.id,
                tag_id=tags_dict[tag_data.name].id
            )
            for tag_data in question_create.tags
        ]
        session.add_all(question_tags)

    session.commit()
    session.refresh(question)

    return QuestionRead(
        id=question.id,
        prompt=question.prompt,
        media_url=question.media_url,
        explanation=question.explanation,
        answerChoices=answer_choices,
        tags=list(tags_dict.values()) if tags_dict else None,
        deleted_at=question.deleted_at
    )


@router.put('/{question_id}', response_model=QuestionRead)
def update_question(*, session: SessionDep, question_id: uuid.UUID, question_in: QuestionUpdate):
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Update basic question fields
    update_dict = question_in.model_dump(
        exclude_unset=True, exclude={'tags', 'answerChoices'})
    question.sqlmodel_update(update_dict)

    # Handle tags update
    if question_in.tags is not None:
        tag_names = [tag_data.name for tag_data in question_in.tags]
        existing_tags = session.exec(
            select(Tag).where(Tag.name.in_(tag_names))
        ).all()

        # Validate all tags exist
        if len(existing_tags) != len(tag_names):
            found_names = {tag.name for tag in existing_tags}
            missing = set(tag_names) - found_names
            raise HTTPException(
                status_code=400,
                detail=f"Tags do not exist: {', '.join(missing)}"
            )

        # Replace all question-tag relationships
        session.exec(
            select(Question_Tags).where(
                Question_Tags.question_id == question_id)
        ).all()  # Trigger delete cascade

        session.query(Question_Tags).filter(
            Question_Tags.question_id == question_id
        ).delete()

        new_relationships = [
            Question_Tags(question_id=question_id, tag_id=tag.id)
            for tag in existing_tags
        ]
        session.add_all(new_relationships)

    # Handle answer choices update
    if question_in.answerChoices is not None:
        # Delete old and create new in one transaction
        session.query(Answer_Choice).filter(
            Answer_Choice.question_id == question_id
        ).delete()

        new_choices = [
            Answer_Choice(
                text=ac.text,
                is_correct=ac.is_correct,
                question_id=question_id
            )
            for ac in question_in.answerChoices
        ]
        session.add_all(new_choices)

    session.commit()

    # Fetch complete question data for response
    answer_choices = session.exec(
        select(Answer_Choice).where(Answer_Choice.question_id == question_id)
    ).all()

    question_tag_links = session.exec(
        select(Question_Tags).where(Question_Tags.question_id == question_id)
    ).all()

    tags = []
    if question_tag_links:
        tag_ids = [qt.tag_id for qt in question_tag_links]
        tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()

    return QuestionRead(
        id=question.id,
        prompt=question.prompt,
        media_url=question.media_url,
        explanation=question.explanation,
        answerChoices=answer_choices,
        tags=tags or None,
        deleted_at=question.deleted_at
    )


@router.delete('/{question_id}')
def soft_delete_question(session: SessionDep, question_id: uuid.UUID):
    question = session.get(Question, question_id)
    if not question or question.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Question not found")

    question.deleted_at = datetime.now(UTC)
    session.add(question)
    session.commit()
    return {'message': 'Question soft deleted successfully'}


@router.delete('/{question_id}/hard')
def hard_delete_question(session: SessionDep, question_id: uuid.UUID):
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Delete the question (CASCADE will delete related answer_choices and question_tags)
    session.delete(question)
    session.commit()
    return {'message': 'Question permanently deleted'}
