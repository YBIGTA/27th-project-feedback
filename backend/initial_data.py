from sqlalchemy.orm import Session

from .database import SessionLocal
from . import models

# 삽입할 초기 학년 데이터 목록
GRADES_DATA = [
    {"grade_id": 1, "grade_name": "초등학교 1학년"},
    {"grade_id": 2, "grade_name": "초등학교 2학년"},
    {"grade_id": 3, "grade_name": "초등학교 3학년"},
    {"grade_id": 4, "grade_name": "초등학교 4학년"},
    {"grade_id": 5, "grade_name": "초등학교 5학년"},
    {"grade_id": 6, "grade_name": "초등학교 6학년"},
    {"grade_id": 7, "grade_name": "중학교 1학년"},
    {"grade_id": 8, "grade_name": "중학교 2학년"},
    {"grade_id": 9, "grade_name": "중학교 3학년"},
    {"grade_id": 10, "grade_name": "고등학교 1학년"},
    {"grade_id": 11, "grade_name": "고등학교 2학년"},
    {"grade_id": 12, "grade_name": "고등학교 3학년"},
    {"grade_id": 13, "grade_name": "재수생/N수생"},
]

def init_db():
    """
    데이터베이스 초기화 함수.
    grades 테이블에 데이터가 없으면 초기 데이터를 삽입합니다.
    """
    db: Session = SessionLocal()
    try:
        # grades 테이블에 데이터가 있는지 확인
        existing_grade = db.query(models.Grade).first()
        
        # 데이터가 없을 경우에만 실행
        if not existing_grade:
            print("데이터베이스 초기화 시작: grades 테이블에 데이터를 추가합니다.")
            for grade_data in GRADES_DATA:
                grade = models.Grade(**grade_data)
                db.add(grade)
            
            db.commit()
            print("초기 데이터 생성 완료.")
        else:
            print("데이터가 이미 존재하므로 초기화를 건너뜁니다.")

    finally:
        db.close()
