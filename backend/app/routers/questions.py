import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from sqlmodel import select

from app.audit import get_audit_context, record_audit_event
from app.db.database import SessionDep
from app.models import (
    Answer_Choice,
    Question,
    QuestionCreate,
    QuestionCreateResponse,
    QuestionRead,
    QuestionUpdate,
    Questions,
    Tag,
    Question_Tag,
)
from app.storage import delete_media, get_bucket, get_signing_credentials


router = APIRouter(prefix="/questions", tags=["questions"])


def _serialize_question(question: Question):
    return {
        "id": str(question.id),
        "base_question_id": (
            str(question.base_question_id) if question.base_question_id else None
        ),
        "version": question.version,
        "prompt": question.prompt,
        "media_content_type": question.media_content_type,
        "explanation": question.explanation,
        "created_at": question.created_at.isoformat() if question.created_at else None,
        "updated_at": question.updated_at.isoformat() if question.updated_at else None,
        "deleted_at": question.deleted_at.isoformat() if question.deleted_at else None,
    }


def _serialize_question_state(session, question_id: uuid.UUID):
    question = session.get(Question, question_id)
    if not question:
        return None

    answer_choices = session.exec(
        select(Answer_Choice).where(Answer_Choice.question_id == question_id)
    ).all()
    question_tag_links = session.exec(
        select(Question_Tag).where(Question_Tag.question_id == question_id)
    ).all()
    tags = []
    if question_tag_links:
        tag_ids = [qt.tag_id for qt in question_tag_links]
        tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()

    return {
        **_serialize_question(question),
        "answerChoices": [
            {"id": str(ac.id), "text": ac.text, "is_correct": ac.is_correct}
            for ac in answer_choices
        ],
        "tags": [{"id": str(tag.id), "name": tag.name} for tag in tags],
    }


@router.get("/")
def read_questions(session: SessionDep):
    # Only return the latest version of each question (by base_question_id or id)
    all_questions = session.exec(
        select(Question).where(Question.deleted_at.is_(None))
    ).all()

    latest_questions = {}
    for q in all_questions:
        base_id = q.base_question_id or q.id
        if (
            base_id not in latest_questions
            or q.version > latest_questions[base_id].version
        ):
            latest_questions[base_id] = q

    questions = list(latest_questions.values())
    count = len(questions)

    if not questions:
        return Questions(data=[], count=0)

    # Fetch and group all answer choices
    answer_choices = session.exec(select(Answer_Choice)).all()
    answer_choices_by_question = defaultdict(list)
    for ac in answer_choices:
        answer_choices_by_question[ac.question_id].append(ac)

    # Fetch and group all tags
    question_tag = session.exec(select(Question_Tag)).all()
    tags = session.exec(select(Tag)).all()
    tags_by_id = {tag.id: tag for tag in tags}

    tags_by_question = defaultdict(list)
    for qt in question_tag:
        if qt.tag_id in tags_by_id:
            tags_by_question[qt.question_id].append(tags_by_id[qt.tag_id])

    # Build response objects
    questions_data = [
        QuestionRead(
            id=q.id,
            prompt=q.prompt,
            media_content_type=q.media_content_type,
            explanation=q.explanation,
            answerChoices=answer_choices_by_question[q.id],
            tags=tags_by_question[q.id] or None,
            deleted_at=q.deleted_at,
        )
        for q in questions
    ]

    return Questions(data=questions_data, count=count)


@router.get("/{question_id}", response_model=QuestionRead)
def read_question_by_id(question_id: uuid.UUID, session: SessionDep):
    question = session.get(Question, question_id)
    if not question or question.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Question not found")

    # Fetch answer choices for this question
    answer_choices = session.exec(
        select(Answer_Choice).where(Answer_Choice.question_id == question_id)
    ).all()

    # Fetch tags for this question
    question_tag = session.exec(
        select(Question_Tag).where(Question_Tag.question_id == question_id)
    ).all()

    tags = []
    if question_tag:
        tag_ids = [qt.tag_id for qt in question_tag]
        tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()

    return QuestionRead(
        id=question.id,
        prompt=question.prompt,
        media_content_type=question.media_content_type,
        explanation=question.explanation,
        answerChoices=answer_choices,
        tags=tags or None,
        deleted_at=question.deleted_at,
    )


@router.post("/", response_model=QuestionCreateResponse)
def create_question(
    *,
    session: SessionDep,
    request: Request,
    question_in: QuestionCreate,
    content_type: str | None = None,
):
    question_create = QuestionCreate.model_validate(question_in)

    # Validate and fetch all tags in one query
    tags_dict = {}
    if question_create.tags:
        tag_names = [tag_data.name for tag_data in question_create.tags]
        existing_tags = session.exec(select(Tag).where(Tag.name.in_(tag_names))).all()
        tags_dict = {tag.name: tag for tag in existing_tags}

        # Check if any tags are missing
        missing_tags = set(tag_names) - set(tags_dict.keys())
        if missing_tags:
            raise HTTPException(
                status_code=400, detail=f"Tags do not exist: {', '.join(missing_tags)}"
            )

    # Create question
    question = Question.model_validate(question_create)
    session.add(question)
    session.flush()  # Get question.id without committing

    # Batch create answer choices
    answer_choices = [
        Answer_Choice(text=ac.text, is_correct=ac.is_correct, question_id=question.id)
        for ac in question_create.answerChoices
    ]
    session.add_all(answer_choices)

    # Batch create question-tag relationships
    if question_create.tags:
        question_tag = [
            Question_Tag(question_id=question.id, tag_id=tags_dict[tag_data.name].id)
            for tag_data in question_create.tags
        ]
        session.add_all(question_tag)

    session.commit()
    session.refresh(question)

    # Refresh answer choices to get their IDs
    for ac in answer_choices:
        session.refresh(ac)

    # Fetch tags for this question
    question_tag_links = session.exec(
        select(Question_Tag).where(Question_Tag.question_id == question.id)
    ).all()

    tags = []
    if question_tag_links:
        tag_ids = [qt.tag_id for qt in question_tag_links]
        tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()

    upload_url = None
    if content_type:
        filename = f"questions/{question.id}"
        blob = get_bucket().blob(filename)
        upload_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type=content_type,
            credentials=get_signing_credentials(),
        )
        question.media_content_type = content_type
        session.add(question)
        session.commit()

    context = get_audit_context(request)
    record_audit_event(
        session,
        context=context,
        action="question.create",
        entity_type="question",
        entity_id=question.id,
        after=_serialize_question_state(session, question.id),
    )
    session.commit()

    return QuestionCreateResponse(
        id=question.id,
        prompt=question.prompt,
        media_content_type=question.media_content_type,
        explanation=question.explanation,
        answerChoices=answer_choices,
        tags=tags or None,
        deleted_at=question.deleted_at,
        upload_url=upload_url,
    )


@router.put("/{question_id}", response_model=QuestionCreateResponse)
def update_question(
    *,
    session: SessionDep,
    request: Request,
    question_id: uuid.UUID,
    question_in: QuestionUpdate,
    content_type: str | None = None,
):
    old_question = session.get(Question, question_id)
    if not old_question:
        raise HTTPException(status_code=404, detail="Question not found")

    before_snapshot = _serialize_question_state(session, question_id)

    # Create a new version of the question
    base_id = (
        old_question.base_question_id
        if old_question.base_question_id
        else old_question.id
    )
    new_version = old_question.version + 1

    # Build the new question data
    update_dict = question_in.model_dump(
        exclude_unset=True, exclude={"tags", "answerChoices"}
    )

    # Always explicitly set media_content_type from request (allow None to delete)
    # If a new upload is requested, prefer the upload content type.
    new_media_content_type = content_type or question_in.media_content_type

    # Create new question with updated fields
    new_question = Question(
        prompt=update_dict.get("prompt", old_question.prompt),
        media_content_type=new_media_content_type,
        explanation=update_dict.get("explanation", old_question.explanation),
        updated_at=datetime.now(UTC),
        version=new_version,
        base_question_id=base_id,
    )
    session.add(new_question)
    session.flush()  # Get new question ID

    # Handle tags - copy from old or use new
    if question_in.tags is not None:
        tag_names = [tag_data.name for tag_data in question_in.tags]
        existing_tags = session.exec(select(Tag).where(Tag.name.in_(tag_names))).all()

        # Validate all tags exist
        if len(existing_tags) != len(tag_names):
            found_names = {tag.name for tag in existing_tags}
            missing = set(tag_names) - found_names
            raise HTTPException(
                status_code=400, detail=f"Tags do not exist: {', '.join(missing)}"
            )

        new_relationships = [
            Question_Tag(question_id=new_question.id, tag_id=tag.id)
            for tag in existing_tags
        ]
        session.add_all(new_relationships)
    else:
        # Copy tags from old question
        old_question_tag = session.exec(
            select(Question_Tag).where(Question_Tag.question_id == question_id)
        ).all()

        new_relationships = [
            Question_Tag(question_id=new_question.id, tag_id=qt.tag_id)
            for qt in old_question_tag
        ]
        session.add_all(new_relationships)

    # Handle answer choices - copy from old or use new
    if question_in.answerChoices is not None:
        new_choices = [
            Answer_Choice(
                text=ac.text, is_correct=ac.is_correct, question_id=new_question.id
            )
            for ac in question_in.answerChoices
        ]
        session.add_all(new_choices)
    else:
        # Copy answer choices from old question
        old_answer_choices = session.exec(
            select(Answer_Choice).where(Answer_Choice.question_id == question_id)
        ).all()

        new_choices = [
            Answer_Choice(
                text=ac.text, is_correct=ac.is_correct, question_id=new_question.id
            )
            for ac in old_answer_choices
        ]
        session.add_all(new_choices)

    upload_url = None
    if content_type:
        # Generate a signed upload URL for the newly versioned question ID.
        filename = f"questions/{new_question.id}"
        blob = get_bucket().blob(filename)
        upload_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=15),
            method="PUT",
            content_type=content_type,
            credentials=get_signing_credentials(),
        )
    elif old_question.media_content_type and new_media_content_type:
        # Preserve media across versions by copying the old object's bytes
        # from questions/{old_id} to questions/{new_id}.
        old_filename = f"questions/{old_question.id}"
        new_filename = f"questions/{new_question.id}"
        bucket = get_bucket()
        old_blob = bucket.blob(old_filename)
        if old_blob.exists():
            bucket.copy_blob(old_blob, bucket, new_filename)
        else:
            # Avoid stale media metadata when storage object is missing.
            new_question.media_content_type = None

    session.commit()
    session.refresh(new_question)

    context = get_audit_context(request)
    record_audit_event(
        session,
        context=context,
        action="question.update",
        entity_type="question",
        entity_id=new_question.id,
        before=before_snapshot,
        after=_serialize_question_state(session, new_question.id),
        metadata={
            "previous_question_id": str(old_question.id),
            "base_question_id": str(base_id),
            "new_version": new_version,
        },
    )
    session.commit()

    # Refresh answer choices to get their IDs
    for ac in new_choices:
        session.refresh(ac)

    # Fetch complete question data for response
    answer_choices = session.exec(
        select(Answer_Choice).where(Answer_Choice.question_id == new_question.id)
    ).all()

    question_tag_links = session.exec(
        select(Question_Tag).where(Question_Tag.question_id == new_question.id)
    ).all()

    tags = []
    if question_tag_links:
        tag_ids = [qt.tag_id for qt in question_tag_links]
        tags = session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()

    return QuestionCreateResponse(
        id=new_question.id,
        prompt=new_question.prompt,
        media_content_type=new_question.media_content_type,
        explanation=new_question.explanation,
        answerChoices=answer_choices,
        tags=tags or None,
        deleted_at=new_question.deleted_at,
        upload_url=upload_url,
    )


@router.delete("/{question_id}")
def soft_delete_question(session: SessionDep, request: Request, question_id: uuid.UUID):
    question = session.get(Question, question_id)
    if not question or question.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Question not found")

    before_snapshot = _serialize_question_state(session, question_id)
    question.deleted_at = datetime.now(UTC)
    session.add(question)
    context = get_audit_context(request)
    record_audit_event(
        session,
        context=context,
        action="question.delete",
        entity_type="question",
        entity_id=question.id,
        before=before_snapshot,
        after=_serialize_question_state(session, question_id),
        metadata={"delete_type": "soft"},
    )
    session.commit()
    return {"message": "Question soft deleted successfully"}


@router.delete("/{question_id}/hard")
def hard_delete_question(session: SessionDep, request: Request, question_id: uuid.UUID):
    question = session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    before_snapshot = _serialize_question_state(session, question_id)

    # Delete media from storage if it exists
    if question.media_content_type:
        delete_media(f"questions/{question_id}")

    # Delete the question (CASCADE will delete related answer_choices and question_tag)
    session.delete(question)
    context = get_audit_context(request)
    record_audit_event(
        session,
        context=context,
        action="question.delete",
        entity_type="question",
        entity_id=question_id,
        before=before_snapshot,
        after=None,
        metadata={"delete_type": "hard"},
    )
    session.commit()
    return {"message": "Question permanently deleted"}
