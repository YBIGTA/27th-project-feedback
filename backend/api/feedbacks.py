from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..database import get_db
from ..feedback_ai import generate_ai_feedback
from .auth import get_current_teacher

router = APIRouter(
    prefix="/api/v1/students", # 공통 경로
    tags=["feedbacks"],
)

@router.post("/{student_id}/feedbacks", response_model=schemas.Class)
def create_feedback_for_student(
    student_id: int,
    request: schemas.FeedbackCreateRequest,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """
    특정 학생의 수업 기록 및 AI 피드백을 생성하는 API
    """
    # 학생이 현재 로그인한 선생님의 학생이 맞는지 확인
    db_student = crud.get_student(db, student_id=student_id, teacher_id=current_teacher.teacher_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found or not authorized")

    # 수업 및 피드백 생성
    created_class = crud.create_class_and_feedback(
        db=db,
        student_id=student_id,
        teacher_id=current_teacher.teacher_id,
        class_info=request.class_info,
        feedback_info=request.feedback_info
    )

    # AI 피드백 생성 로직
    ai_comments = generate_ai_feedback(
        student_id=student_id,
        db=db,
        current_class_info=request.class_info.dict(),
        current_scores=request.feedback_info.dict()
    )

    # AI 코멘트 업데이트
    crud.update_feedback_with_ai_comment(
        db=db,
        feedback_id=created_class.feedback.feedback_id,
        ai_comments=ai_comments,
        teacher_id=current_teacher.teacher_id
    )
    
    db.refresh(created_class)
    return created_class

@router.get("/{student_id}/feedbacks", response_model=List[schemas.Feedback])
def read_student_feedbacks(
    student_id: int, 
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):    
    """
    특정 학생의 전체 피드백 목록 조회
    """
    # 학생 소유권 확인
    db_student = crud.get_student(db, student_id=student_id, teacher_id=current_teacher.teacher_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found or not authorized")
    
    feedbacks = crud.get_feedbacks_by_student(db, student_id=student_id)
    return feedbacks