import re
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from . import crud, models
from core_logic import feedback_system

def _convert_orm_to_dict(past_classes: List[models.Class]) -> List[Dict]:
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
                "progress_text": cls.progress_text,
                "class_memo": cls.class_memo,
            })
    return sorted(records, key=lambda x: x['date'])

def _parse_ai_response(ai_response_text: str) -> Dict[str, str]:
    """
    구분자를 사용하여 AI 응답을 안정적으로 파싱하고 후처리합니다.
    """
    try:
        # 구분자로 섹션 분리
        sections = ai_response_text.split("|||SECTION_SEPARATOR|||")
        
        if len(sections) == 3:
            improvement = sections[0].strip()
            attitude = sections[1].strip()
            overall = sections[2].strip()
            
            # 각 섹션에서 제목 부분 제거 (예: "**1. 수업보완: 부족한 부분과 개선 방향**")
            improvement = re.sub(r'^\*\*.*?\*\*', '', improvement).strip()
            attitude = re.sub(r'^\*\*.*?\*\*', '', attitude).strip()
            overall = re.sub(r'^\*\*.*?\*\*', '', overall).strip()
            
            return {"improvement": improvement, "attitude": attitude, "overall": overall}
        else:
            print(f"\n--- AI 응답 섹션 개수 불일치: {len(sections)}개 ---")
            print(ai_response_text)
            print("------------------------\n")
            return {
                "improvement": "AI 응답 형식이 올바르지 않습니다.",
                "attitude": "섹션 개수를 확인해주세요.",
                "overall": ai_response_text
            }

    except Exception as e:
        print(f"\n--- AI 응답 파싱 실패: {e} ---")
        print(ai_response_text)
        print("------------------------\n")
        return {
            "improvement": "AI 응답을 파싱할 수 없습니다.",
            "attitude": "형식을 확인해주세요.",
            "overall": ai_response_text
        }

def generate_ai_feedback(
    student_id: int,
    db: Session,
    current_class_info: Dict,
    current_scores: Dict
) -> Dict[str, str]:
    """
    DB에서 데이터를 조회하고, 공유 로직(FeedbackAnalyzer)을 호출하여
    AI 피드백을 생성합니다.
    """
    student_orm = crud.get_student(db, student_id)
    past_classes_orm = crud.get_student_past_classes(db, student_id)
    
    past_records_dict = _convert_orm_to_dict(list(reversed(past_classes_orm)))
    student_info_dict = {"name": student_orm.name, "grade": student_orm.grade}
    
    current_full_info = {**current_class_info, **current_scores}

    analyzer = feedback_system.FeedbackSystem()

    ai_response_text = analyzer.generate_feedback(
        student_info=student_info_dict,
        current_class_info=current_full_info,
        past_records=past_records_dict
    )
    
    return _parse_ai_response(ai_response_text)