from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db
from .auth import get_current_teacher

router = APIRouter(
    prefix="/api/v1/feedbacks",
    tags=["feedback_details"],
)

@router.get("/{feedback_id}", response_model=schemas.Feedback)
def read_feedback(
    feedback_id: int, 
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """
    ID로 특정 피드백 조회
    """
    db_feedback = crud.get_feedback(
        db, feedback_id=feedback_id, teacher_id=current_teacher.teacher_id
    )
    if db_feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found or not authorized")
    return db_feedback


@router.put("/{feedback_id}", response_model=schemas.Feedback)
def update_feedback(
    feedback_id: int, 
    feedback_update: schemas.FeedbackUpdate, 
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """
    특정 피드백 정보 수정
    """
    db_feedback = crud.update_feedback(
        db, 
        feedback_id=feedback_id, 
        feedback_update=feedback_update, 
        teacher_id=current_teacher.teacher_id
    )
    if db_feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found or not authorized")
    return db_feedback