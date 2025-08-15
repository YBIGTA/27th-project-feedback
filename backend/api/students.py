from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/v1/students",
    tags=["students"],
)

@router.post("", response_model=schemas.Student, status_code=201)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    """
    신규 학생 생성
    """
    return crud.create_student(db=db, student=student)


@router.get("", response_model=List[schemas.Student])
def read_students(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    전체 학생 목록 조회
    """
    students = crud.get_students(db, skip=skip, limit=limit)
    return students

@router.get("/{student_id}", response_model=schemas.Student)
def read_student(student_id: int, db: Session = Depends(get_db)):
    """
    ID로 특정 학생 정보 조회
    """
    db_student = crud.get_student(db, student_id=student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student


@router.put("/{student_id}", response_model=schemas.Student)
def update_student(student_id: int, student_update: schemas.StudentUpdate, db: Session = Depends(get_db)):
    """
    특정 학생 정보 수정 (이름, 학년)
    """
    db_student = crud.update_student(db, student_id=student_id, student_update=student_update)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """
    특정 학생 정보 삭제
    """
    db_student = crud.delete_student(db, student_id=student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)