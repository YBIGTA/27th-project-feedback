# 이 파일은 실제 AI 모델을 호출하지 않는 테스트용 Mock 파일입니다.
# API 연결 테스트를 위해 고정된 더미 데이터를 즉시 반환합니다.

import time

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
