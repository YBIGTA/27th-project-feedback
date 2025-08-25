#!/usr/bin/env python3
"""
math_feedback_cleaned.csv 파일을 RDS로 옮기는 마이그레이션 스크립트 (v3)
student_id를 문자열에서 숫자로 변환하여 처리
"""

import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import pymysql
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import URL
import numpy as np
import re

def load_environment():
    """환경 변수를 로드합니다."""
    load_dotenv()
    
    db_config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'port': int(os.getenv('DB_PORT', 3306))
    }
    
    print("🔧 환경 변수 확인:")
    for key, value in db_config.items():
        if key == 'password':
            print(f"  {key}: {'*' * len(str(value)) if value else 'None'}")
        else:
            print(f"  {key}: {value}")
    
    return db_config

def create_database_connection(db_config):
    """데이터베이스 연결을 생성합니다."""
    try:
        # SQLAlchemy 엔진 생성
        url = URL.create(
            drivername="mysql+pymysql",
            username=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database']
        )
        
        engine = create_engine(url, echo=False)
        print("✅ SQLAlchemy 엔진 생성 성공!")
        
        return engine
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

def load_csv_data(csv_file):
    """CSV 파일을 로드하고 데이터를 분석합니다."""
    print(f"\n📊 CSV 파일 로드 중: {csv_file}")
    
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ CSV 파일 로드 성공!")
        print(f"  총 레코드 수: {len(df)}")
        print(f"  고유 학생 수: {df['student_id'].nunique()}")
        print(f"  학년 종류: {sorted(df['grade'].unique())}")
        
        # student_id를 숫자로 변환
        print(f"\n🔄 student_id 변환 중...")
        df['student_id_numeric'] = df['student_id'].apply(lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else None)
        
        # 변환 결과 확인
        print(f"  원본 student_id 예시: {df['student_id'].head().tolist()}")
        print(f"  변환된 student_id 예시: {df['student_id_numeric'].head().tolist()}")
        
        # 컬럼 정보 출력
        print(f"\n📋 컬럼 정보:")
        for col in df.columns:
            print(f"  {col}: {df[col].dtype}")
        
        return df
        
    except Exception as e:
        print(f"❌ CSV 파일 로드 실패: {e}")
        return None

def get_existing_grades_mapping(engine):
    """기존 grades 테이블의 데이터를 가져와서 매핑을 생성합니다."""
    print(f"\n🔍 기존 grades 데이터 확인 중...")
    
    try:
        with engine.connect() as conn:
            # 기존 grades 데이터 조회
            result = conn.execute(text("SELECT grade_id, grade_name FROM grades ORDER BY grade_id"))
            grades = result.fetchall()
            
            print(f"기존 grades 데이터:")
            for grade in grades:
                print(f"  ID {grade[0]}: {grade[1]}")
            
            # CSV 학년과 기존 grades 매핑
            grade_mapping = {}
            
            # CSV의 학년을 기존 grades와 매칭
            csv_grade_to_db_grade = {
                '중1': '중학교 1학년',
                '중2': '중학교 2학년', 
                '중3': '중학교 3학년',
                '고1': '고등학교 1학년',
                '고2': '고등학교 2학년',
                '고3': '고등학교 3학년'
            }
            
            for csv_grade, db_grade_name in csv_grade_to_db_grade.items():
                # 기존 grades에서 해당 학년명 찾기
                matching_grade = None
                for grade in grades:
                    if db_grade_name in grade[1] or grade[1] in db_grade_name:
                        matching_grade = grade
                        break
                
                if matching_grade:
                    grade_mapping[csv_grade] = matching_grade[0]
                    print(f"  ✅ {csv_grade} → {matching_grade[1]} (ID: {matching_grade[0]})")
                else:
                    print(f"  ❌ {csv_grade}에 매칭되는 grades를 찾을 수 없음")
            
            return grade_mapping
            
    except Exception as e:
        print(f"❌ grades 데이터 확인 실패: {e}")
        return None

def create_teacher(engine):
    """기본 선생님을 생성합니다."""
    print(f"\n👨‍🏫 선생님 데이터 생성 중...")
    
    try:
        with engine.connect() as conn:
            # 기본 선생님 데이터
            teacher_data = {
                'name': '테스트 선생님',
                'email': 'test@example.com',
                'hashed_password': 'hashed_password_placeholder'
            }
            
            # 선생님이 이미 존재하는지 확인
            result = conn.execute(text("SELECT teacher_id FROM teachers WHERE email = :email"), 
                                {"email": teacher_data['email']})
            existing_teacher = result.fetchone()
            
            if existing_teacher:
                teacher_id = existing_teacher[0]
                print(f"  ✅ 기존 선생님 사용: ID {teacher_id}")
            else:
                # 새 선생님 생성
                result = conn.execute(text("""
                    INSERT INTO teachers (name, email, hashed_password) 
                    VALUES (:name, :email, :hashed_password)
                """), teacher_data)
                teacher_id = conn.execute(text("SELECT LAST_INSERT_ID()")).fetchone()[0]
                print(f"  ✅ 새 선생님 생성: ID {teacher_id}")
            
            conn.commit()
            return teacher_id
            
    except Exception as e:
        print(f"❌ 선생님 생성 실패: {e}")
        return None

def migrate_students(engine, df, teacher_id, grade_mapping):
    """학생 데이터를 마이그레이션합니다."""
    print(f"\n👥 학생 데이터 마이그레이션 중...")
    
    try:
        with engine.connect() as conn:
            # 고유한 학생 목록 추출 (변환된 student_id 사용)
            unique_students = df[['student_id_numeric', 'student_name', 'grade']].drop_duplicates()
            
            migrated_count = 0
            for _, student in unique_students.iterrows():
                student_id = student['student_id_numeric']
                name = student['student_name']
                grade_name = student['grade']
                
                if pd.isna(student_id):
                    print(f"  ⚠️  student_id 변환 실패: {name}")
                    continue
                
                # 학년 ID 매핑
                grade_id = grade_mapping.get(grade_name)
                if not grade_id:
                    print(f"  ⚠️  알 수 없는 학년: {grade_name} (학생: {name})")
                    continue
                
                # 학생이 이미 존재하는지 확인
                result = conn.execute(text("SELECT student_id FROM students WHERE student_id = :student_id"), 
                                    {"student_id": student_id})
                if result.fetchone():
                    print(f"  ✅ 학생 이미 존재: {name} (ID: {student_id})")
                    continue
                
                # 새 학생 생성
                conn.execute(text("""
                    INSERT INTO students (student_id, teacher_id, name, grade_id) 
                    VALUES (:student_id, :teacher_id, :name, :grade_id)
                """), {
                    "student_id": student_id,
                    "teacher_id": teacher_id,
                    "name": name,
                    "grade_id": grade_id
                })
                
                migrated_count += 1
                print(f"  ✅ 학생 생성: {name} (ID: {student_id}, 학년: {grade_name})")
            
            conn.commit()
            print(f"  🎉 총 {migrated_count}명의 학생 마이그레이션 완료!")
            return True
            
    except Exception as e:
        print(f"❌ 학생 마이그레이션 실패: {e}")
        return False

def migrate_classes_and_feedbacks(engine, df, teacher_id):
    """수업 및 피드백 데이터를 마이그레이션합니다."""
    print(f"\n📚 수업 및 피드백 데이터 마이그레이션 중...")
    
    try:
        with engine.connect() as conn:
            migrated_classes = 0
            migrated_feedbacks = 0
            
            for _, row in df.iterrows():
                # student_id 변환 확인
                student_id = row['student_id_numeric']
                if pd.isna(student_id):
                    continue
                
                # 날짜 파싱
                try:
                    class_date = pd.to_datetime(row['date']).date()
                except:
                    print(f"  ⚠️  날짜 파싱 실패: {row['date']}")
                    continue
                
                # 수업 데이터 생성
                class_data = {
                    'student_id': student_id,
                    'teacher_id': teacher_id,
                    'subject': row['subject'],
                    'class_date': class_date,
                    'progress_text': row['progress_text'] if pd.notna(row['progress_text']) else None,
                    'class_memo': row['class_memo'] if pd.notna(row['class_memo']) else None
                }
                
                # 수업 생성
                result = conn.execute(text("""
                    INSERT INTO classes (student_id, teacher_id, subject, class_date, progress_text, class_memo)
                    VALUES (:student_id, :teacher_id, :subject, :class_date, :progress_text, :class_memo)
                """), class_data)
                
                class_id = conn.execute(text("SELECT LAST_INSERT_ID()")).fetchone()[0]
                migrated_classes += 1
                
                # 피드백 데이터 생성
                feedback_data = {
                    'class_id': class_id,
                    'attitude_score': int(row['attitude_score']) if pd.notna(row['attitude_score']) else 3,
                    'understanding_score': int(row['understanding_score']) if pd.notna(row['understanding_score']) else 3,
                    'homework_score': int(row['homework_score']) if pd.notna(row['homework_score']) else 3,
                    'qa_score': int(row['qa_score']) if pd.notna(row['qa_score']) else 3,
                    'ai_comment_improvement': row['수업보완'] if pd.notna(row['수업보완']) else None,
                    'ai_comment_attitude': row['수업태도'] if pd.notna(row['수업태도']) else None,
                    'ai_comment_overall': row['전체수업 Comment'] if pd.notna(row['전체수업 Comment']) else None
                }
                
                # 피드백 생성
                conn.execute(text("""
                    INSERT INTO feedbacks (class_id, attitude_score, understanding_score, homework_score, qa_score, 
                                        ai_comment_improvement, ai_comment_attitude, ai_comment_overall)
                    VALUES (:class_id, :attitude_score, :understanding_score, :homework_score, :qa_score,
                           :ai_comment_improvement, :ai_comment_attitude, :ai_comment_overall)
                """), feedback_data)
                
                migrated_feedbacks += 1
                
                if migrated_classes % 10 == 0:
                    print(f"  진행률: {migrated_classes}/{len(df)}")
            
            conn.commit()
            print(f"  🎉 수업 {migrated_classes}개, 피드백 {migrated_feedbacks}개 마이그레이션 완료!")
            return True
            
    except Exception as e:
        print(f"❌ 수업 및 피드백 마이그레이션 실패: {e}")
        return False

def verify_migration(engine):
    """마이그레이션 결과를 검증합니다."""
    print(f"\n🔍 마이그레이션 결과 검증 중...")
    
    try:
        with engine.connect() as conn:
            # 각 테이블의 데이터 수 확인
            tables = ['teachers', 'students', 'grades', 'classes', 'feedbacks']
            
            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                count = result.fetchone()[0]
                print(f"  {table}: {count}개")
            
            # 샘플 데이터 확인
            print(f"\n📊 샘플 데이터 확인:")
            
            # 학생 샘플
            result = conn.execute(text("SELECT * FROM students LIMIT 3"))
            students = result.fetchall()
            print(f"  학생 샘플: {len(students)}개")
            
            # 수업 샘플
            result = conn.execute(text("SELECT * FROM classes LIMIT 3"))
            classes = result.fetchall()
            print(f"  수업 샘플: {len(classes)}개")
            
            # 피드백 샘플
            result = conn.execute(text("SELECT * FROM feedbacks LIMIT 3"))
            feedbacks = result.fetchall()
            print(f"  피드백 샘플: {len(feedbacks)}개")
            
            return True
            
    except Exception as e:
        print(f"❌ 마이그레이션 검증 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("🎯 CSV to RDS 마이그레이션 도구 (v3)")
    print("=" * 60)
    
    csv_file = "data/math_feedback_cleaned.csv"
    
    # 1. 환경 변수 로드
    db_config = load_environment()
    
    # 2. 데이터베이스 연결
    engine = create_database_connection(db_config)
    if not engine:
        return
    
    # 3. CSV 데이터 로드 및 student_id 변환
    df = load_csv_data(csv_file)
    if df is None:
        return
    
    # 4. 기존 grades 데이터와 매핑 생성
    grade_mapping = get_existing_grades_mapping(engine)
    if not grade_mapping:
        print("❌ grades 매핑을 생성할 수 없습니다")
        return
    
    # 5. 선생님 생성
    teacher_id = create_teacher(engine)
    if teacher_id is None:
        return
    
    # 6. 학생 데이터 마이그레이션
    if not migrate_students(engine, df, teacher_id, grade_mapping):
        return
    
    # 7. 수업 및 피드백 데이터 마이그레이션
    if not migrate_classes_and_feedbacks(engine, df, teacher_id):
        return
    
    # 8. 마이그레이션 결과 검증
    verify_migration(engine)
    
    print(f"\n🎉 마이그레이션 완료!")
    print(f"CSV 파일: {csv_file}")
    print(f"RDS 데이터베이스: {db_config['database']}")

if __name__ == "__main__":
    main()
