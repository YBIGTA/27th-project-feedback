# 이 파일은 실제 AI 모델을 호출하지 않는 테스트용 Mock 파일입니다.
# API 연결 테스트를 위해 고정된 더미 데이터를 즉시 반환합니다.

import time
from sqlalchemy.orm import Session
from .. import crud, models
# 공유 로직 모듈을 import 합니다.
from .. import feedback_system

def generate_ai_feedback(student_info, current_scores, past_classes):
    """
    AI 피드백 생성을 흉내 내는 Mock 함수
    입력 데이터를 기반으로 간단한 테스트용 코멘트 생성
    """
    print("========== Mock AI Feedback Generator ==========")
    print(f"학생 이름: {student_info.name}")
    print(f"현재 점수: {current_scores.dict()}")
    print(f"과거 기록 개수: {len(past_classes)}개")
    print("==============================================")

    # 더미 데이터 반환
    mock_response = {
        "improvement": (
            f"[테스트 응답] {student_info.name} 학생의 수업 보완점입니다. "
            f"이해도는 {current_scores.understanding_score}점이었습니다. "
            "이 부분은 Mock 데이터이며, 실제 AI 응답이 아닙니다."
        ),
        "attitude": (
            f"[테스트 응답] {student_info.name} 학생의 수업 태도입니다. "
            f"태도 점수는 {current_scores.attitude_score}점이었습니다. "
            "API 연결 테스트가 성공적으로 수행되었습니다."
        ),
        "overall": (
            "[테스트 응답] 전체 코멘트입니다. "
            "이 메시지가 보인다면, FastAPI 엔드포인트와 AI 모듈이 "
            "정상적으로 연결된 것입니다."
        )
    }

    return mock_response

def _convert_orm_to_dict(past_classes: list[models.Class]) -> list[dict]:
    """SQLAlchemy ORM 객체 리스트를 표준 딕셔너리 리스트로 변환합니다."""
    records = []
    for cls in past_classes:
        if cls.feedback:
            records.append({
                "date": cls.class_date,
                "attitude_score": cls.feedback.attitude_score,
                "understanding_score": cls.feedback.understanding_score,
                "homework_score": cls.feedback.homework_score,
                "qa_score": cls.feedback.qa_score,
                "progress_text": cls.progress_text
            })
    # 날짜순으로 정렬 (오래된 것이 먼저 오도록)
    return sorted(records, key=lambda x: x['date'])

def generate_ai_feedback(
    student_id: int,
    db: Session,
    current_class_info: dict,
    current_scores: dict
):
    # 1. DB에서 데이터 조회 (SQLAlchemy 객체)
    student_orm = crud.get_student(db, student_id)
    past_classes_orm = crud.get_student_past_classes(db, student_id)

    # 2. 표준 형식(딕셔너리 리스트)으로 변환 (어댑터 역할)
    past_records_dict = _convert_orm_to_dict(past_classes_orm)
    student_info_dict = {"name": student_orm.name, "grade": student_orm.grade}

    # 3. 공유 로직 호출
    final_prompt = feedback_analyzer.create_feedback_prompt(
        student_info=student_info_dict,
        current_class_info=current_class_info,
        current_scores=current_scores,
        past_records=past_records_dict
    )

    # 4. AI 호출 및 결과 반환
    # ai_response = feedback_analyzer.invoke_ai(final_prompt)
    # return _parse_ai_response(ai_response)
    print("===== Generated Prompt for Backend =====")
    print(final_prompt)
    return {"improvement": "백엔드 테스트 응답", "attitude": "성공", "overall": "완료"}
