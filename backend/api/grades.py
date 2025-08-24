from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/v1/grades",
    tags=["grades"],
)

@router.get("", response_model=List[schemas.Grade])
def read_grades(db: Session = Depends(get_db)):
    """
    전체 학년 목록 조회
    (학생 생성/수정 시 드롭다운 메뉴를 채우는 데 사용)
    """
    return db.query(models.Grade).order_by(models.Grade.grade_id).all()