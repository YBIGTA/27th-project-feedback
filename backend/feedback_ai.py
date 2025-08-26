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

# def _parse_ai_response(ai_response_text: str) -> Dict[str, str]:
#     """
#     정규 표현식을 사용하여 AI 응답을 안정적으로 파싱하고 후처리합니다.
#     """
#     print(ai_response_text)
#     try:
#         improvement_match = re.search(r"1\..*?(?:수업보완|개선 방향).*?:(.*?)(?=2\..*?(?:수업태도|학습 자세)|$)", ai_response_text, re.DOTALL)
#         attitude_match = re.search(r"2\..*?(?:수업태도|학습 자세).*?:(.*?)(?=3\..*?(?:전체 Comment|종합적 평가)|$)", ai_response_text, re.DOTALL)
#         overall_match = re.search(r"3\..*?(?:전체 Comment|종합적 평가).*?:(.*)", ai_response_text, re.DOTALL)

#         improvement = improvement_match.group(1).strip() if improvement_match else "내용 없음"
#         attitude = attitude_match.group(1).strip() if attitude_match else "내용 없음"
#         overall = overall_match.group(1).strip() if overall_match else "내용 없음"

#         if not improvement and not attitude and not overall:
#              overall = ai_response_text

#         return {"improvement": improvement, "attitude": attitude, "overall": overall}

#     except Exception:
#         print("\n--- AI 응답 파싱 실패 ---")
#         print(ai_response_text)
#         print("------------------------\n")
#         return {
#             "improvement": "AI 응답을 파싱할 수 없습니다.",
#             "attitude": "형식을 확인해주세요.",
#             "overall": ai_response_text
#         }

def _parse_ai_response(ai_response_text: str) -> Dict[str, str]:
    """
    AI 응답을 안정적으로 파싱하고 후처리합니다.
    현재 AI 응답 형식에 최적화되어 있습니다.
    """
    print(f"\n=== AI 응답 파싱 시작 ===")
    print(f"원본 응답: {ai_response_text[:200]}...")
    
    try:
        if "|||SECTION_SEPARATOR|||" in ai_response_text:
            sections = ai_response_text.split("|||SECTION_SEPARATOR|||")
            if len(sections) == 3:
                improvement = sections[0].strip()
                attitude = sections[1].strip()
                overall = sections[2].strip()
                
                # 제목 부분 제거
                improvement = re.sub(r'^\*\*.*?\*\*', '', improvement).strip()
                attitude = re.sub(r'^\*\*.*?\*\*', '', attitude).strip()
                overall = re.sub(r'^\*\*.*?\*\*', '', overall).strip()
                
                print(f"구분자 파싱 성공")
                return {"improvement": improvement, "attitude": attitude, "overall": overall}
        
        return {
            "improvement": "AI 응답을 파싱할 수 없습니다.",
            "attitude": "형식을 확인해주세요.",
            "overall": ai_response_text
        }

    except Exception as e:
        print(f"\n--- AI 응답 파싱 중 예외 발생: {e} ---")
        print(f"원본 응답: {ai_response_text}")
        print("------------------------\n")
        return {
            "improvement": "AI 응답을 파싱할 수 없습니다.",
            "attitude": "형식을 확인해주세요.",
            "overall": ai_response_text
        }

def generate_ai_feedback(
    student_id: int,
    teacher_id: int,  # 추가
    db: Session,
    current_class_info: Dict,
    current_scores: Dict
) -> Dict[str, str]:
    """
    DB에서 데이터를 조회하고, 공유 로직(FeedbackAnalyzer)을 호출하여
    AI 피드백을 생성합니다.
    """
    student_orm = crud.get_student(db, student_id, teacher_id)
    past_classes_orm = crud.get_student_past_classes(db, student_id)
    
    past_records_dict = _convert_orm_to_dict(list(reversed(past_classes_orm)))
    grade_info = crud.get_grade(db, student_orm.grade_id)
    student_info_dict = {"name": student_orm.name, "grade": grade_info.grade_name}
    
    current_full_info = {**current_class_info, **current_scores}

    analyzer = feedback_system.FeedbackSystem()

    ai_response_text = analyzer.generate_feedback(
        student_info=student_info_dict,
        current_class_info=current_full_info,
        past_records=past_records_dict
    )
    
    return _parse_ai_response(ai_response_text)