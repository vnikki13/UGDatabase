import uuid
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..db.database import SessionDep
from ..models import Tag, TagBase, TagCreate, TagUpdate


router = APIRouter(
    prefix='/tags',
    tags=['tags']
)


@router.get('/')
def read_tags(session: SessionDep):
    tags = session.exec(select(Tag)).all()
    return tags


@router.get('/{tag_id}', response_model=TagBase)
def read_tag_by_id(tag_id: uuid.UUID, session: SessionDep):
    tag = session.get(Tag, tag_id)
    return tag


@router.post('/', response_model=TagCreate)
def create_tag(*, session: SessionDep, tag_in: TagCreate):
    tag_create = TagCreate.model_validate(tag_in)
    tag = Tag.model_validate(tag_create)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.put('/{tag_id}', response_model=TagUpdate)
def update_tag(*, session: SessionDep, tag_id: uuid.UUID, tag_in: TagUpdate):
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    update_tag = tag_in.model_dump(exclude_unset=True)
    tag.sqlmodel_update(update_tag)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


@router.delete('/{tag_id}')
def delete_tag(session: SessionDep, tag_id: uuid.UUID):
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    session.delete(tag)
    session.commit()
    return {'message': 'Tag deleted successfully'}
