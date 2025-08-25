#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV → RDS(MySQL) 마이그레이션 스크립트 (스키마: students/classes/feedbacks)

필요 .env:
DB_HOST=xxx.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=your_password
DB_NAME=feedback_system

CSV 컬럼(헤더) 예시:
student_name,grade,subject,class_date,progress_text,class_memo,
attitude_score,understanding_score,homework_score,qa_score,
ai_comment_improvement,ai_comment_attitude,ai_comment_overall
"""

import os
import sys
import time
from typing import Optional, Dict, Tuple

import pandas as pd
from dotenv import load_dotenv

from sqlalchemy import (
    create_engine, Column, Integer, String, Date, DateTime, Text, ForeignKey,
    UniqueConstraint, text
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.engine import URL
from datetime import datetime, date

# ---------- 설정 ----------
CSV_PATH = os.getenv("CSV_PATH", "data/math_feedback.csv")
BATCH_SIZE = 500  # 커밋 주기
# -------------------------

Base = declarative_base()

# ---------- 모델 (주신 스키마 그대로) ----------
class Student(Base):
    __tablename__ = "students"
    student_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    grade = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    classes = relationship("Class", back_populates="student", cascade="all, delete-orphan")

    # (선택) 동일 이름+학년 중복 방지를 위한 보조 유니크
    #__table_args__ = (UniqueConstraint("name", "grade", name="uq_students_name_grade"),)


class Class(Base):
    __tablename__ = "classes"
    class_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(50), nullable=False)
    class_date = Column(Date, nullable=False)
    progress_text = Column(String(255), nullable=True)
    class_memo = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    student = relationship("Student", back_populates="classes")
    feedbacks = relationship("Feedback", back_populates="clazz", cascade="all, delete-orphan")

    # 한 학생이 같은 날짜에 같은 과목을 여러 번 수강할 수 있음 (오전/오후, 1교시/2교시 등)
    # 유니크 제약조건 없음


class Feedback(Base):
    __tablename__ = "feedbacks"
    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("classes.class_id", ondelete="CASCADE"), nullable=False)
    attitude_score = Column(Integer, nullable=True)
    understanding_score = Column(Integer, nullable=True)
    homework_score = Column(Integer, nullable=True)
    qa_score = Column(Integer, nullable=True)
    ai_comment_improvement = Column(Text, nullable=True)
    ai_comment_attitude = Column(Text, nullable=True)
    ai_comment_overall = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    clazz = relationship("Class", back_populates="feedbacks")

    # (선택) 수업 1건당 피드백 1개 제약
    #__table_args__ = (UniqueConstraint("class_id", name="uq_feedbacks_class_id"),)
# ------------------------------------------------


def _load_env():
    load_dotenv()
    req = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing = [k for k in req if not os.getenv(k)]
    if missing:
        raise RuntimeError(f".env 누락: {', '.join(missing)}")


def _sqlalchemy_url(db_name: Optional[str]) -> str:
    return URL.create(
        "mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=db_name
    )


def _ensure_database_exists():
    """DB가 없으면 생성"""
    target_db = os.getenv("DB_NAME")
    # 서버(기본 mysql DB)로 먼저 접속
    engine_root = create_engine(_sqlalchemy_url(None), pool_pre_ping=True, isolation_level="AUTOCOMMIT")
    with engine_root.connect() as conn:
        rows = conn.execute(text("SHOW DATABASES;")).fetchall()
        dbs = {r[0] for r in rows}
        if target_db not in dbs:
            print(f"📦 데이터베이스가 없어 생성합니다: {target_db}")
            conn.execute(text(
                f"CREATE DATABASE `{target_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            ))
        else:
            print(f"✅ 데이터베이스 존재: {target_db}")
            
            # 기존 테이블이 있다면 삭제 (완전히 새로 시작)
            print("🗑️  기존 테이블 정리 중...")
            try:
                conn.execute(text(f"USE `{target_db}`"))
                conn.execute(text("DROP TABLE IF EXISTS feedbacks"))
                conn.execute(text("DROP TABLE IF EXISTS classes"))
                conn.execute(text("DROP TABLE IF EXISTS students"))
                print("✅ 기존 테이블 삭제 완료")
            except Exception as e:
                print(f"⚠️  테이블 삭제 중 오류 (무시): {e}")


def _get_engine_and_session():
    engine = create_engine(_sqlalchemy_url(os.getenv("DB_NAME")), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return engine, SessionLocal


def _parse_date(v) -> date:
    if pd.isna(v) or v == "":
        return None
    # ISO, yyyy-mm-dd, yyyy/m/d 등 유연 처리
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%y-%m-%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(str(v), fmt).date()
        except ValueError:
            continue
    # pandas가 datetime으로 파싱한 경우
    if isinstance(v, pd.Timestamp):
        return v.date()
    # 최후: to_datetime 시도
    try:
        return pd.to_datetime(v).date()
    except Exception:
        raise ValueError(f"날짜 파싱 실패: {v}")


def migrate(csv_path: str = CSV_PATH):
    _load_env()
    _ensure_database_exists()

    engine, SessionLocal = _get_engine_and_session()

    print("🔧 테이블 생성(존재하지 않으면)...")
    Base.metadata.create_all(bind=engine)
    print("✅ 테이블 준비 완료")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    print(f"📖 CSV 로딩: {csv_path}")
    df = pd.read_csv(csv_path)

    # # 필수 컬럼 체크
    # required_cols = [
    #     "student_name", "grade", "subject", "class_date",
    #     "attitude_score", "understanding_score", "homework_score", "qa_score"
    # ]
    # missing_cols = [c for c in required_cols if c not in df.columns]
    # if missing_cols:
    #     raise ValueError(f"CSV 필수 컬럼 누락: {missing_cols}")

    # 결측치 기본값
    text_cols_default = {
        "progress_text": "",
        "class_memo": "",
        "ai_comment_improvement": "",
        "ai_comment_attitude": "",
        "ai_comment_overall": ""
    }
    for c, default in text_cols_default.items():
        if c in df.columns:
            df[c] = df[c].fillna(default)
        else:
            df[c] = default

    # 캐시(성능): 이미 삽입한 학생/수업 키를 메모리에 저장
    student_cache: Dict[Tuple[str, int], int] = {}
    class_cache: Dict[Tuple[int, str, date], int] = {}

    session = SessionLocal()
    inserted_students = 0
    inserted_classes = 0
    inserted_feedbacks = 0

    t0 = time.time()
    try:
        print("🔄 마이그레이션 시작...")
        # 1) 선행으로 기존 학생/수업 키 캐싱(옵션) — 큰 데이터셋이면 생략 가능
        # 학생 캐시
        for name, grade in session.query(Student.name, Student.grade).all():
            student_cache[(name, grade)] = session.query(Student.student_id).filter_by(name=name, grade=grade).first()[0]
        # 수업 캐시 (progress_text 포함)
        for sid, subject, cdate, ptext, cid in session.query(
            Class.student_id, Class.subject, Class.class_date, Class.progress_text, Class.class_id
        ).all():
            class_cache[(sid, subject, cdate, ptext)] = cid

        # 2) 행 단위 처리
        for i, row in df.iterrows():
            name = str(row["student_name"]).strip()
            grade = parse_grade(row["grade"])
            subject = str(row["subject"]).strip()
            cdate = _parse_date(row["date"])
            progress_text = str(row.get("progress_text", "")).strip()

            # --- 학생 upsert (name+grade 고유) ---
            skey = (name, grade)
            student_id = student_cache.get(skey)
            if student_id is None:
                # DB에 존재 여부 1차 확인(유니크 제약 대비)
                existing = session.query(Student).filter_by(name=name, grade=grade).first()
                if existing:
                    student_id = existing.student_id
                else:
                    s = Student(name=name, grade=grade)
                    session.add(s)
                    session.flush()  # PK 발급
                    student_id = s.student_id
                    inserted_students += 1
                student_cache[skey] = student_id

            # --- 수업 upsert (student_id+subject+class_date+progress_text 고유) ---
            # 같은 날짜에 같은 과목을 여러 번 수강할 수 있음 (오전/오후, 1교시/2교시 등)
            ckey = (student_id, subject, cdate, progress_text)
            class_id = class_cache.get(ckey)
            if class_id is None:
                existing_cls = session.query(Class).filter_by(
                    student_id=student_id,
                    subject=subject,
                    class_date=cdate,
                    progress_text=progress_text
                ).first()
                if existing_cls:
                    class_id = existing_cls.class_id
                    # 기존 수업 정보 업데이트 (선택사항)
                    if existing_cls.progress_text != progress_text:
                        existing_cls.progress_text = progress_text
                    if existing_cls.class_memo != row.get("class_memo", ""):
                        existing_cls.class_memo = row.get("class_memo", "")
                else:
                    cls = Class(
                        student_id=student_id,
                        subject=subject,
                        class_date=cdate,
                        progress_text=progress_text,
                        class_memo=row.get("class_memo", "")
                    )
                    session.add(cls)
                    session.flush()
                    class_id = cls.class_id
                    inserted_classes += 1
                class_cache[ckey] = class_id

            # --- 피드백 upsert (class_id 고유) ---
            fb = session.query(Feedback).filter_by(class_id=class_id).first()
            if fb is None:
                fb = Feedback(
                    class_id=class_id,
                    attitude_score=int(row["attitude_score"]) if not pd.isna(row["attitude_score"]) else None,
                    understanding_score=int(row["understanding_score"]) if not pd.isna(row["understanding_score"]) else None,
                    homework_score=int(row["homework_score"]) if not pd.isna(row["homework_score"]) else None,
                    qa_score=int(row["qa_score"]) if not pd.isna(row["qa_score"]) else None,
                    ai_comment_improvement=row.get("수업보완", "") if not pd.isna(row.get("수업보완", "")) else "",
                    ai_comment_attitude=row.get("수업태도", "") if not pd.isna(row.get("수업태도", "")) else "",
                    ai_comment_overall=row.get("전체수업 Comment", "") if not pd.isna(row.get("전체수업 Comment", "")) else ""
                )
                session.add(fb)
                inserted_feedbacks += 1
            else:
                print(f"피드백 갱신: class_id={class_id}")  # 디버깅용 로그
                # 이미 있으면 갱신(원치 않으면 이 블록 제거)
                fb.attitude_score = int(row["attitude_score"]) if not pd.isna(row["attitude_score"]) else fb.attitude_score
                fb.understanding_score = int(row["understanding_score"]) if not pd.isna(row["understanding_score"]) else fb.understanding_score
                fb.homework_score = int(row["homework_score"]) if not pd.isna(row["homework_score"]) else fb.homework_score
                fb.qa_score = int(row["qa_score"]) if not pd.isna(row["qa_score"]) else fb.qa_score
                fb.ai_comment_improvement = row.get("ai_comment_improvement", fb.ai_comment_improvement) if not pd.isna(row.get("ai_comment_improvement", "")) else fb.ai_comment_improvement
                fb.ai_comment_attitude = row.get("ai_comment_attitude", fb.ai_comment_attitude) if not pd.isna(row.get("ai_comment_attitude", "")) else fb.ai_comment_attitude
                fb.ai_comment_overall = row.get("ai_comment_overall", fb.ai_comment_overall) if not pd.isna(row.get("ai_comment_overall", "")) else fb.ai_comment_overall

            if (i + 1) % BATCH_SIZE == 0:
                session.commit()
                print(f"  • 진행률 {i + 1}/{len(df)} (학생 +{inserted_students}, 수업 +{inserted_classes}, 피드백 +{inserted_feedbacks})")

        session.commit()
        dt = time.time() - t0
        print(f"✅ 완료: 학생 {inserted_students} / 수업 {inserted_classes} / 피드백 {inserted_feedbacks} (총 {len(df)}행) | {dt:.1f}s")
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()


def parse_grade(grade_str: str) -> int:
    """'초1' → 1, '중1' → 7, '고1' → 10 등으로 변환"""
    grade_str = str(grade_str).strip()
    if grade_str.startswith("초"):
        return int(grade_str[1:])
    elif grade_str.startswith("중"):
        return 6 + int(grade_str[1:])
    elif grade_str.startswith("고"):
        return 9 + int(grade_str[1:])
    else:
        # 숫자만 있거나 예외 처리
        try:
            return int(grade_str)
        except Exception:
            raise ValueError(f"학년 변환 실패: {grade_str}")


def main():
    try:
        print("🚀 CSV → RDS 마이그레이션 시작")
        migrate(CSV_PATH)
        print("🎉 마이그레이션 성공")
    except OperationalError as e:
        print("💥 RDS 연결 실패(OperationalError):", e)
        print(" - RDS 상태/보안그룹/엔드포인트/.env를 다시 확인하세요.")
    except SQLAlchemyError as e:
        print("💥 SQLAlchemy 에러:", e)
    except Exception as e:
        print("💥 예기치 못한 에러:", e)


if __name__ == "__main__":
    main()