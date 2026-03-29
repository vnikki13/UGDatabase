from fastapi import APIRouter, HTTPException

from app.clients.ghost import get_ghost_client


router = APIRouter(
    prefix='/ghost',
    tags=['ghost']
)


@router.get('/users')
def get_users():
    """Get all admin Ghost users"""
    try:
        client = get_ghost_client()
        return client.get_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/users/{user_email}')
def get_user(user_email: str):
    """Get a specific Ghost user by email"""
    try:
        client = get_ghost_client()
        return client.validate_user_by_email(user_email)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/members/{member_id}")
def get_member(member_id: str):
    """Get a specific Ghost member by member ID"""
    try:
        client = get_ghost_client()
        return client.get_member(member_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/members")
def search_member(search: str):
    """Search for a Ghost member using any form of identification"""
    try:
        client = get_ghost_client()
        return client.search_member(search)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
