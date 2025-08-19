from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import get_db
from ..feedback_ai import generate_ai_feedback

router = APIRouter(
    prefix="/api/v1/students", # 공통 경로
    tags=["feedbacks"],
)

@router.post("/{student_id}/feedbacks", response_model=schemas.Class)
def create_feedback_for_student(
    student_id: int,
    request: schemas.FeedbackCreateRequest,
    db: Session = Depends(get_db)
):
    """
    특정 학생의 수업 기록 및 AI 피드백을 생성하는 API
    """
    db_student = crud.get_student(db, student_id=student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    created_class = crud.create_class_and_feedback(
        db=db,
        student_id=student_id,
        class_info=request.class_info,
        feedback_info=request.feedback_info
    )

    past_classes = crud.get_student_past_classes(db, student_id=student_id)

    db_student.progress_text = request.class_info.progress_text
    db_student.class_memo = request.class_info.class_memo
    
    ai_comments = generate_ai_feedback(
        student_id=student_id,
        db=db,
        current_class_info=request.class_info.dict(),
        current_scores=request.feedback_info.dict()
    )

    crud.update_feedback_with_ai_comment(
        db=db,
        feedback_id=created_class.feedback.feedback_id,
        ai_comments=ai_comments
    )
    
    db.refresh(created_class)
    return created_class

@router.get("/{student_id}/feedbacks", response_model=List[schemas.Feedback])
def read_student_feedbacks(student_id: int, db: Session = Depends(get_db)):
    """
    특정 학생의 전체 피드백 목록 조회
    """
    db_student = crud.get_student(db, student_id=student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    
    feedbacks = crud.get_feedbacks_by_student(db, student_id=student_id)
    return feedbacks