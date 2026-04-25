import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from sqlmodel import select, func

from app.db.database import SessionDep
from app.models import Tag, TagBase, TagCreate, TagUpdate


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/")
def read_tags(session: SessionDep):
    tags = session.exec(select(Tag).where(Tag.deleted_at == None)).all()
    return tags


@router.get("/{tag_id}", response_model=TagBase)
def read_tag_by_id(tag_id: uuid.UUID, session: SessionDep):
    tag = session.get(Tag, tag_id)
    if not tag or tag.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.post("/", response_model=TagCreate)
def create_tag(*, session: SessionDep, tag_in: TagCreate):
    tag_create = TagCreate.model_validate(tag_in)

    # Check if a non-deleted tag with the same name (case-insensitive) already exists
    existing_tag = session.exec(
        select(Tag).where(
            func.lower(Tag.name) == tag_create.name.lower(),
            Tag.deleted_at == None,
        )
    ).first()

    if existing_tag:
        raise HTTPException(
            status_code=400, detail=f"Tag '{existing_tag.name}' already exists"
        )

    tag = Tag.model_validate(tag_create)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.put("/{tag_id}", response_model=TagUpdate)
def update_tag(*, session: SessionDep, tag_id: uuid.UUID, tag_in: TagUpdate):
    tag = session.get(Tag, tag_id)
    if not tag or tag.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Tag not found")

    update_data = tag_in.model_dump(exclude_unset=True)
    tag.sqlmodel_update(update_data)
    tag.updated_at = datetime.now(timezone.utc)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.delete("/{tag_id}")
def delete_tag(session: SessionDep, tag_id: uuid.UUID):
    tag = session.get(Tag, tag_id)
    if not tag or tag.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Tag not found")

    tag.deleted_at = datetime.now(timezone.utc)
    session.add(tag)
    session.commit()
    return {"message": "Tag deleted successfully"}
