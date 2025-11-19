from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..db.database import SessionDep
from ..models import Member


router = APIRouter(
    prefix='/members',
    tags=['members']
)


@router.get('/')
def read_members(
    session: SessionDep
):
    members = session.exec(select(Member)).all()
    return members


@router.get('/{member_id}')
def read_member_by_id(
    member_id: int,
    session: SessionDep
):
    members = session.get(Member, member_id)
    return members


@router.post('/', response_model=Member)
def create_member(*, session: SessionDep, member: Member):
    session.add(member)
    session.commit()
    return member


@router.put('/{member_id}', response_model=Member)
def update_member(*, session: SessionDep, member_id: int, member_in: Member):
    member = session.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    update_dict = member_in.model_dump(exclude_unset=True)
    member.sqlmodel_update(update_dict)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.delete('/{member_id}')
def delete_member(session: SessionDep, member_id: int):
    member = session.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    session.delete(member)
    session.commit()
    return {'message': 'Member deleted successfully'}
