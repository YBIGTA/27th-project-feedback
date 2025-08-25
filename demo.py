"""
수치 데이터를 어떻게 넣을 것인가 고민
1.수치는 비교하기 쉬운만큼 학생의 추이를 보는데 적극적으로 사용하자
2.수치들을 미리 계산한 추이를 전달하여 llm은 학생의 태도, 이해도 등에 대한 변화에 주목하게 하자.

수업보완:관리교사 코멘트, 수치 정보에서 부족한점을 찾도록
수업태도:점수 기반
전체수업:수업내용 + 점수 추이,변화

"""

# deps: pip install upstage langchain langgraph pydantic

import os
import pandas as pd
from typing import Dict, Any, List
from pydantic import SecretStr
from langgraph.graph import StateGraph, END
import streamlit as st


# ----- LLM (Upstage) -----
from langchain_upstage import ChatUpstage


def get_llm(model: str = "solar-pro-250422", temperature: float = 0.2) -> ChatUpstage:
    if not api_key:
        raise RuntimeError("UPSTAGE_API_KEY 환경변수가 필요합니다.")
    return ChatUpstage(model=model, temperature=temperature, api_key=api_key)


# ----- CSV 데이터 로드 및 학생 데이터 추출 -----
def load_math_feedback_data(csv_path: str = "math_feedback.csv") -> pd.DataFrame:
    """CSV 파일을 로드합니다."""
    return pd.read_csv(csv_path)


def get_student_data_by_index(
    csv_index: int, df: pd.DataFrame = None
) -> List[Dict[str, Any]]:
    """
    CSV의 특정 index(행 번호)를 입력받아, 해당 행의 학생 이름과 날짜를 찾고
    그 학생의 해당 날짜 이전 수업 기록들만 가져와서 demo.py의 기존 형식에 맞게 변환합니다.
    """
    if df is None:
        df = load_math_feedback_data()

    # CSV index 범위 확인
    if csv_index < 0 or csv_index >= len(df):
        raise ValueError(
            f"CSV index {csv_index}가 범위를 벗어났습니다. (0-{len(df)-1})"
        )

    # 해당 index의 학생 이름과 날짜 가져오기
    target_row = df.iloc[csv_index]
    target_student_name = target_row["student_name"]
    target_date = target_row["date"]

    # 같은 이름의 학생 데이터 중에서 target_date 이전 데이터만 필터링
    student_data = df[
        (df["student_name"] == target_student_name) & (df["date"] <= target_date)
    ].copy()

    if student_data.empty:
        raise ValueError(
            f"학생 이름 {target_student_name}의 {target_date} 이전 데이터를 찾을 수 없습니다."
        )

    # 기존 demo.py 형식에 맞게 변환
    result = []
    for _, row in student_data.iterrows():
        record = {
            "date": row["date"],
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "grade": row["grade"],
            "subject": row["subject"],
            "attendance": row["attendance"],
            "attitude_score": row["attitude_score"],
            "understanding_score": row["understanding_score"],
            "homework_score": row["homework_score"],
            "qna_difficulty_score": row[
                "qa_score"
            ],  # CSV의 qa_score를 qna_difficulty_score로 매핑
            "progress_text": row["progress_text"],
            "absence_reason": (
                row["absence_reason"] if pd.notna(row["absence_reason"]) else ""
            ),
            "class_memo": row["class_memo"] if pd.notna(row["class_memo"]) else "",
            "수업보완": row["수업보완"] if pd.notna(row["수업보완"]) else "",
            "수업태도": row["수업태도"] if pd.notna(row["수업태도"]) else "",
            "전체수업_Comment": (
                row["전체수업 Comment"] if pd.notna(row["전체수업 Comment"]) else ""
            ),
        }
        result.append(record)

    # 날짜순으로 정렬 (오래된 것부터)
    result.sort(key=lambda x: x["date"])
    return result


def get_student_data_by_id(
    student_id: str, df: pd.DataFrame = None
) -> List[Dict[str, Any]]:
    """
    특정 student_id의 모든 수업 기록을 가져와서 demo.py의 기존 형식에 맞게 변환합니다.
    (기존 호환성을 위해 유지)
    """
    if df is None:
        df = load_math_feedback_data()

    # 해당 학생의 데이터 필터링
    student_data = df[df["student_id"] == student_id].copy()

    if student_data.empty:
        raise ValueError(f"학생 ID {student_id}에 대한 데이터를 찾을 수 없습니다.")

    # 기존 demo.py 형식에 맞게 변환
    result = []
    for _, row in student_data.iterrows():
        record = {
            "date": row["date"],
            "student_id": row["student_id"],
            "student_name": row["student_name"],
            "grade": row["grade"],
            "subject": row["subject"],
            "attendance": row["attendance"],
            "attitude_score": row["attitude_score"],
            "understanding_score": row["understanding_score"],
            "homework_score": row["homework_score"],
            "qna_difficulty_score": row[
                "qa_score"
            ],  # CSV의 qa_score를 qna_difficulty_score로 매핑
            "progress_text": row["progress_text"],
            "absence_reason": (
                row["absence_reason"] if pd.notna(row["absence_reason"]) else ""
            ),
            "class_memo": row["class_memo"] if pd.notna(row["class_memo"]) else "",
            "수업보완": row["수업보완"] if pd.notna(row["수업보완"]) else "",
            "수업태도": row["수업태도"] if pd.notna(row["수업태도"]) else "",
            "전체수업_Comment": (
                row["전체수업 Comment"] if pd.notna(row["전체수업 Comment"]) else ""
            ),
        }
        result.append(record)

    # 날짜순으로 정렬 (오래된 것부터)
    result.sort(key=lambda x: x["date"])
    return result


# ----- 1) 숫자만 처리: 오늘 vs 이전 -----
from typing import Dict, Any
from statistics import mean


def numeric_trend_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    입력:
      state['student_data'] = data와 같은 형태의 학생 전체 기록 리스트
      (텍스트, 숫자 데이터 모두 포함된 전체 학습 기록)
    출력:
      state['numeric_trend'] = 각 지표별 today, prev, diff, trend, past_avg
    """
    raw_data = state.get("student_data", [])
    if len(raw_data) < 2:
        raise ValueError("비교를 위해 최소 2회 수업 데이터가 필요합니다.")

    # 날짜순으로 정렬 (오래된 것부터)
    hist = sorted(raw_data, key=lambda x: x["date"])
    prev, today = hist[-2], hist[-1]
    metrics = {
        "attitude": "attitude_score",
        "understanding": "understanding_score",
        "homework": "homework_score",
        "qna_difficulty": "qna_difficulty_score",
    }

    result = {}
    for k, f in metrics.items():
        t = int(today[f])
        p = int(prev[f])
        d = t - p
        trend = "상승" if d > 0 else ("하락" if d < 0 else "변화 없음")

        # 오늘 이전 모든 점수의 평균
        past_vals = [int(r[f]) for r in hist[:-1]]
        past_avg = round(mean(past_vals), 2) if past_vals else t

        result[k] = {
            "today": t,
            "prev": p,
            "diff": d,
            "trend": trend,
            "past_avg": past_avg,
        }

    state["numeric_trend"] = result
    return state


# ----- 2) 숫자 → 추이 설명(텍스트 위주, LLM 사용) -----
def trend_explainer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    입력: state['numeric_trend']
    출력: state['numeric_trend_text']
    - 규칙: 오늘 기준으로 이전 대비 변화 설명. 지표명 고정 4개.
    """
    nt = state.get("numeric_trend")
    if not nt:
        raise ValueError(
            "numeric_trend가 없습니다. numeric_trend_node를 먼저 호출하세요."
        )

    # 프롬프트(시스템+유저). 텍스트 위주, 숫자는 근거로만.
    system_msg = (
        "너는 교사용 요약 비서다. 주어진 점수에서 직전 수업 대비 변화를 "
        "교사가 학부모에게 전달할 수 있는 간결한 한국어로 작성한다. 과장/모호어 금지. 한 항목당 1문장."
    )
    user_msg = f"""[지표 데이터]
- 수업태도(attitude): today={nt['attitude']['today']}, prev={nt['attitude']['prev']}, diff={nt['attitude']['diff']}, trend={nt['attitude']['trend']}, past_avg={nt['attitude']['past_avg']}
- 수업이해도(understanding): today={nt['understanding']['today']}, prev={nt['understanding']['prev']}, diff={nt['understanding']['diff']}, trend={nt['understanding']['trend']}, past_avg={nt['understanding']['past_avg']}
- 과제평가(homework): today={nt['homework']['today']}, prev={nt['homework']['prev']}, diff={nt['homework']['diff']}, trend={nt['homework']['trend']}, past_avg={nt['homework']['past_avg']}
- 질문난이도(qna_difficulty): today={nt['qna_difficulty']['today']}, prev={nt['qna_difficulty']['prev']}, diff={nt['qna_difficulty']['diff']}, trend={nt['qna_difficulty']['trend']}, past_avg={nt['qna_difficulty']['past_avg']}



[작성 규칙]

1. 점수가 이전 수업이나 과거 평균보다 1점 이상 차이 날 경우, 오늘을 기준으로 이전 대비 어떻게 달라졌는지를 구체적으로 언급.

2. 점수가 변화가 없더라도, 현재 상태를 잘 유지하는지 / 부족한 점이 지속되는지를 해석 가이드에 맞춰 명확히 언급.

3. 각 항목은 1문장, 총 4문장 작성. 점수는 직접 언급하지 않음.

4. 해석은 아래의 항목별 해석 가이드를 기반으로 구체적으로 기술.

5. 문장은 부드럽지만 명확하게 작성. 

6. 문장에 ‘수업태도’, ‘수업이해도’, ‘과제평가’, ‘질문난이도’ 등 항목명을 직접 사용하지 않음. 대신 행동·태도·변화 상황을 묘사하는 표현을 사용.

### 예시:

변화 있는 경우 → "수업에 적극적으로 임하며 참여하는 모습이 점점 더 활발해지고 있습니다."

변화 없는 경우 → "기초와 응용을 균형 있게 묻는 질문을 꾸준히 이어가고 있습니다." / "집중이 잘 되지 않는 모습이 이어지고 있어 추가 지도가 필요합니다."

### 해석 가이드
수업 태도
5점: 수업 전반에 활발히 참여하며, 질문과 의견 제시로 분위기를 이끎.
4점: 대부분 성실하게 임하며, 잠깐 흐트러져도 곧 집중을 회복함.
3점: 참여 의지는 있으나 발언 빈도가 낮아 추가적인 참여 유도가 필요함.
2점: 집중 유지가 어렵고 참여가 소극적이어서 지속적인 관심과 지원이 필요함.
1점: 수업 몰입도와 참여도가 매우 낮아 목표 달성을 위해 강력한 지도·관리가 요구됨.

수업 이해도
5점: 학습 내용을 깊이 있게 파악하고, 변형·응용 과제도 스스로 해결함.
4점: 핵심 내용을 잘 이해하며, 기본 수준의 응용 문제는 큰 어려움 없이 수행함.
3점: 기초 개념은 이해하나, 난도가 높은 문제 해결에는 도움을 필요로 함.
2점: 주요 개념 이해가 미흡해 반복 학습과 추가 자료 지원이 필요함.
1점: 전반적인 기초부터 재학습이 필요한 수준임.

과제 수행
5점: 모든 과제를 정성껏 완수하며, 정확성과 완성도가 높고 제출 기한을 지킴.
4점: 대부분 수행하였으나 일부 세부 사항에서 실수나 누락이 있음.
3점: 과제의 절반 이상을 제출했으나 정확성·완성도가 부족함.
2점: 일부만 제출하거나 기한을 지키지 않는 경우가 잦음.
1점: 과제를 거의 제출하지 않거나 미제출함.

질문(상호작용)
5점: 적극적으로 질문하며, 질문의 내용이 심화적임
4점: 빈번하게 질문하며, 질문의 내용이 기초, 응용 수준임
3점: 질문하기는 하되, 질문의 내용이 기초적인 수준임
2점: 질문이 거의 없으며, 질문의 내용이 수업과 무관함
1점: 질문이 없으며, 교수자의 질문에도 대답을 거의 하지 않음

위 규칙을 지켜 4문장으로 출력만 해줘.
"""
    llm = get_llm()
    resp = llm.invoke([("system", system_msg), ("user", user_msg)])
    # langchain 메시지 객체에서 콘텐츠만 추출
    text = resp.content if hasattr(resp, "content") else str(resp)

    state["numeric_trend_text"] = text.strip()
    return state


# ----- 3) 그래프 연결 -----
def build_graph():
    g = StateGraph(dict)
    g.add_node("numeric_trend", numeric_trend_node)
    g.add_node("trend_text", trend_explainer_node)
    g.set_entry_point("numeric_trend")
    g.add_edge("numeric_trend", "trend_text")
    g.add_edge("trend_text", END)
    return g.compile()


# ----- Index 기반 학생 데이터 분석 함수 -----
def analyze_student_by_index(csv_index: int) -> Dict[str, Any]:
    """
    CSV index를 받아서 해당 학생의 수치 데이터를 분석하고 추이를 제공합니다.
    """
    # 원본 CSV에서 해당 index의 정보 가져오기
    df = load_math_feedback_data()
    target_session_info = df.iloc[csv_index]

    # CSV에서 학생 데이터 로드 (해당 날짜 이전 기록들)
    student_data = get_student_data_by_index(csv_index)

    # 그래프 생성 및 실행
    graph = build_graph()
    state = {"student_data": student_data}
    result = graph.invoke(state)

    return {
        "csv_index": csv_index,
        "student_name": (
            student_data[0]["student_name"] if student_data else "알 수 없음"
        ),
        "student_id": student_data[0]["student_id"] if student_data else "알 수 없음",
        "total_sessions": len(student_data),
        "numeric_trend": result["numeric_trend"],
        "trend_analysis": result["numeric_trend_text"],
        "latest_session": student_data[-1] if student_data else None,
        "target_session_info": {
            "date": target_session_info["date"],
            "grade": target_session_info["grade"],
            "subject": target_session_info["subject"],
            "attendance": target_session_info["attendance"],
            "attitude_score": target_session_info["attitude_score"],
            "understanding_score": target_session_info["understanding_score"],
            "homework_score": target_session_info["homework_score"],
            "qa_score": target_session_info["qa_score"],
            "progress_text": target_session_info["progress_text"],
            "absence_reason": (
                target_session_info["absence_reason"]
                if pd.notna(target_session_info["absence_reason"])
                else ""
            ),
            "class_memo": (
                target_session_info["class_memo"]
                if pd.notna(target_session_info["class_memo"])
                else ""
            ),
            "수업보완": (
                target_session_info["수업보완"]
                if pd.notna(target_session_info["수업보완"])
                else ""
            ),
            "수업태도": (
                target_session_info["수업태도"]
                if pd.notna(target_session_info["수업태도"])
                else ""
            ),
            "전체수업_Comment": (
                target_session_info["전체수업 Comment"]
                if pd.notna(target_session_info["전체수업 Comment"])
                else ""
            ),
        },
    }


# ----- 예시 실행 -----
if __name__ == "__main__":
    # 예시: CSV의 5번째 행(index=5)에 있는 학생 분석
    csv_index = 25  # 원하는 CSV 행 번호

    try:
        result = analyze_student_by_index(csv_index)
        target_info = result["target_session_info"]

        print("=== 분석 대상 ===")
        print(f"CSV Index: {result['csv_index']}")
        print(f"학생 이름: {result['student_name']}")
        print(f"학생 ID: {result['student_id']}")
        print(f"분석 기준 날짜: {target_info['date']}")
        print(f"학년: {target_info['grade']}")
        print(f"과목: {target_info['subject']}")
        print(f"출석상태: {target_info['attendance']}")
        print(f"총 수업 횟수 (해당 날짜까지): {result['total_sessions']}")

        print("\n=== 해당 수업의 점수 ===")
        print(f"수업태도: {target_info['attitude_score']}")
        print(f"수업이해도: {target_info['understanding_score']}")
        print(f"과제평가: {target_info['homework_score']}")
        print(f"질문/답변: {target_info['qa_score']}")

        print("\n=== 해당 수업의 레포트 ===")
        print(f"진도: {target_info['progress_text']}")
        if target_info["absence_reason"]:
            print(f"결석사유: {target_info['absence_reason']}")
        if target_info["class_memo"]:
            print(f"수업메모: {target_info['class_memo']}")
        if target_info["수업보완"]:
            print(f"수업보완: {target_info['수업보완']}")
        if target_info["수업태도"]:
            print(f"수업태도 상세: {target_info['수업태도']}")
        if target_info["전체수업_Comment"]:
            print(f"전체 코멘트: {target_info['전체수업_Comment']}")

        print("\n=== 수치 추이 분석 (해당 날짜까지의 추이) ===")
        for metric, values in result["numeric_trend"].items():
            print(
                f"{metric}: 오늘={values['today']}, 이전={values['prev']}, 차이={values['diff']}, 추이={values['trend']}, 과거평균={values['past_avg']}"
            )

        print("\n=== LLM 분석 결과 ===")
        print(result["trend_analysis"])

    except Exception as e:
        print(f"오류 발생: {e}")

    # 다른 index로도 테스트 가능
    # result2 = analyze_student_by_index(10)
    # print("\n" + "="*50)
    # print(result2["trend_analysis"])
