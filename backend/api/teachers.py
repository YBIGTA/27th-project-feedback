from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas
from .auth import get_current_teacher

router = APIRouter(
    prefix="/api/v1/teachers",
    tags=["teachers"],
)

@router.get("/me", response_model=schemas.Teacher)
async def read_users_me(current_user: schemas.Teacher = Depends(get_current_teacher)):
    """
    현재 로그인된 사용자의 정보를 반환합니다.
    """
    return current_user