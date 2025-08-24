from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, models
from ..database import get_db
from .auth import get_current_teacher

router = APIRouter(
    prefix="/api/v1/students",
    tags=["students"],
)

@router.post("", response_model=schemas.Student, status_code=201)
def create_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """
    신규 학생 생성
    """
    return crud.create_student(
        db=db, student=student, teacher_id=current_teacher.teacher_id
    )


@router.get("", response_model=List[schemas.Student])
def read_my_students(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """
    전체 학생 목록 조회
    """
    students = crud.get_students_by_teacher(
        db, teacher_id=current_teacher.teacher_id, skip=skip, limit=limit
    )
    return students

@router.get("/{student_id}", response_model=schemas.Student)
def read_student(
    student_id: int, 
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """
    ID로 특정 학생 정보 조회
    """
    db_student = crud.get_student(
        db, student_id=student_id, teacher_id=current_teacher.teacher_id
    )
    if db_student is None:
        # 자신의 학생이 아니거나, 존재하지 않는 학생일 경우
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student


@router.put("/{student_id}", response_model=schemas.Student)
def update_student(
    student_id: int, 
    student_update: schemas.StudentUpdate, 
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):    
    """
    특정 학생 정보 수정 (이름, 학년)
    """
    db_student = crud.update_student(
        db, student_id=student_id, student_update=student_update, teacher_id=current_teacher.teacher_id
    )
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found or not authorized")
    return db_student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(
    student_id: int, 
    db: Session = Depends(get_db),
    current_teacher: models.Teacher = Depends(get_current_teacher)
):
    """
    특정 학생 정보 삭제
    """
    db_student = crud.delete_student(
        db, student_id=student_id, teacher_id=current_teacher.teacher_id
    )
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found or not authorized")
    return Response(status_code=status.HTTP_204_NO_CONTENT)