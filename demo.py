"""
수치 데이터를 어떻게 넣을 것인가 고민
1.수치는 비교하기 쉬운만큼 학생의 추이를 보는데 적극적으로 사용하자
2.수치들을 미리 계산한 추이를 전달하여 llm은 학생의 태도, 이해도 등에 대한 변화에 주목하게 하자.
"""

data = [
    {
        "student_id": "1023",
        "date": "2025-08-07",
        "course": "[1기] 문항로 강사 온라인 멘토링 (수학)",
        "duration_min": "60분",
        "attendance": "출석",
        "attitude_score": "4",
        "understanding_score": "3",
        "homework_score": "5",
        "qna_difficulty_score": "4",
        "topics": "피타고라스 정리 복습, 삼각형의 내심, 삼각형의 외심.",
        "absence_reason": "",
        "manager_comment": "오늘 수업에서 피타고라스 정리 문제풀이에 적극적으로 참여하였으나, 삼각형 외심 성질 문제에서 개념 적용에 어려움을 보임. 문제풀이 시 풀이 과정을 명확히 설명하도록 지도 필요. 피타고라스 응용은 안정적. 외심 성질 적용 과정에서 보조선 설정에 반복 어려움.",
    },
    {
        "student_id": "1023",
        "date": "2025-08-07",
        "course": "[1기] 문항로 강사 온라인 멘토링 (수학)",
        "duration_min": "60분",
        "attendance": "출석",
        "attitude_score": "4",
        "understanding_score": "3",
        "homework_score": "5",
        "qna_difficulty_score": "4",
        "topics": "피타고라스 정리 복습, 삼각형의 내심, 삼각형의 외심",
        "notes": "피타고라스 응용은 안정적. 외심 성질 적용 과정에서 보조선 설정에 반복 어려움.",
        "absence_reason": "-",
        "manager_comment": "오늘 수업에서 피타고라스 정리 문제풀이에 적극적으로 참여하였으나, 삼각형 외심 성질 문제에서 개념 적용에 어려움을 보임. 문제풀이 시 풀이 과정을 명확히 설명하도록 지도 필요.",
        "attachments": "중1_18회차.png",
    },
    {
        "student_id": "1023",
        "date": "2025-08-05",
        "course": "[1기] 문항로 강사 온라인 멘토링 (수학)",
        "duration_min": "60분",
        "attendance": "출석",
        "attitude_score": "5",
        "understanding_score": "4",
        "homework_score": "5",
        "qna_difficulty_score": "4",
        "topics": "피타고라스 정리 기본, 직각삼각형 성질",
        "notes": "수업 내내 적극적으로 발언하며 문제 해결 과정에서 창의적인 접근을 시도함.",
        "absence_reason": "-",
        "manager_comment": "오늘은 높은 집중력을 보여주었고, 과제 수행도 완벽했습니다. 특히 문제 풀이 과정 설명이 명확하고 논리적이었음.",
        "attachments": "중1_17회차.png",
    },
    {
        "student_id": "1023",
        "date": "2025-08-02",
        "course": "[1기] 문항로 강사 온라인 멘토링 (수학)",
        "duration_min": "60분",
        "attendance": "출석",
        "attitude_score": "3",
        "understanding_score": "3",
        "homework_score": "4",
        "qna_difficulty_score": "3",
        "topics": "삼각형의 외심, 보조선 그리기",
        "notes": "수업 초반에는 집중했으나, 후반부에는 피로로 인한 집중 저하가 있었음.",
        "absence_reason": "-",
        "manager_comment": "외심의 성질 이해에 시간이 걸렸으며, 후반부에는 질문이 줄어듦. 집중 지속을 위한 짧은 휴식 제안.",
        "attachments": "중1_16회차.png",
    },
    {
        "student_id": "1023",
        "date": "2025-07-30",
        "course": "[1기] 문항로 강사 온라인 멘토링 (수학)",
        "duration_min": "60분",
        "attendance": "출석",
        "attitude_score": "2",
        "understanding_score": "2",
        "homework_score": "3",
        "qna_difficulty_score": "2",
        "topics": "삼각형의 내심 정의와 성질",
        "notes": "수업 중 딴생각이 잦았고, 과제 수행률이 낮음.",
        "absence_reason": "-",
        "manager_comment": "전반적으로 참여도가 낮아, 개별 질문을 통해 참여를 유도할 필요가 있었음.",
        "attachments": "중1_15회차.png",
    },
    {
        "student_id": "1023",
        "date": "2025-07-28",
        "course": "[1기] 문항로 강사 온라인 멘토링 (수학)",
        "duration_min": "60분",
        "attendance": "출석",
        "attitude_score": "3",
        "understanding_score": "2",
        "homework_score": "4",
        "qna_difficulty_score": "3",
        "topics": "직각삼각형의 성질, 피타고라스 정리",
        "notes": "필기와 청취는 성실하나, 발표나 질문은 거의 하지 않음.",
        "absence_reason": "-",
        "manager_comment": "수동적인 태도를 보였으나 기본 개념 이해는 무난함. 발표 참여를 늘릴 필요가 있음.",
        "attachments": "중1_14회차.png",
    },
]
# deps: pip install upstage langchain langgraph pydantic

import os
from typing import Dict, Any
from pydantic import SecretStr
from langgraph.graph import StateGraph, END

try:
    import streamlit as st  # 선택사항(없으면 무시)
except Exception:

    class _Dummy:
        secrets = {}

    st = _Dummy()

# ----- LLM (Upstage) -----
from langchain_upstage import ChatUpstage  # upstage 공식 langchain 패키지

api_key = ""


def get_llm(model: str = "solar-pro-250422", temperature: float = 0.2) -> ChatUpstage:
    if not api_key:
        raise RuntimeError("UPSTAGE_API_KEY 환경변수가 필요합니다.")
    return ChatUpstage(model=model, temperature=temperature, api_key=api_key)


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
    출력: state['numeric_trend_text'] (Korean, 간결한 문장)
    - 규칙: 오늘 기준으로 이전 대비 변화 설명. 지표명 고정 4개.
    """
    nt = state.get("numeric_trend")
    if not nt:
        raise ValueError(
            "numeric_trend가 없습니다. numeric_trend_node를 먼저 호출하세요."
        )

    # 프롬프트(시스템+유저). 텍스트 위주, 숫자는 근거로만.
    system_msg = (
        "너는 교사용 요약 비서다. 주어진 지표의 오늘 점수와 직전 수업 대비 변화를 "
        "교사가 학부모에게 전달할 수 있는 간결한 한국어로 작성한다. 과장/모호어 금지. 한 항목당 1문장."
    )
    user_msg = f"""[지표 데이터]
- 수업태도(attitude): today={nt['attitude']['today']}, prev={nt['attitude']['prev']}, diff={nt['attitude']['diff']}, trend={nt['attitude']['trend']}, past_avg={nt['attitude']['past_avg']}
- 수업이해도(understanding): today={nt['understanding']['today']}, prev={nt['understanding']['prev']}, diff={nt['understanding']['diff']}, trend={nt['understanding']['trend']}, past_avg={nt['understanding']['past_avg']}
- 과제평가(homework): today={nt['homework']['today']}, prev={nt['homework']['prev']}, diff={nt['homework']['diff']}, trend={nt['homework']['trend']}, past_avg={nt['homework']['past_avg']}
- 질문난이도(qna_difficulty): today={nt['qna_difficulty']['today']}, prev={nt['qna_difficulty']['prev']}, diff={nt['qna_difficulty']['diff']}, trend={nt['qna_difficulty']['trend']}, past_avg={nt['qna_difficulty']['past_avg']}



[작성 규칙]
1) 점수가 이전수업과 과거의 평균보다 1점이상 차이나는 경우에는, 오늘을 기준으로 '이전 대비 어떻게 달라졌는지'를 명확히 쓴다.
2) 아래의 해석 가이드를 따라서 현재 상태가 어떠한지 구체적으로 언급한다.
3) 각 항목 1문장, 총 4문장. 점수 언급 금지.
4) 너무 딱딱하지 않게 말해야한다.
4) 예시: 수업참여가 점점 늘어 수업태도가 좋아지는게 보이고 있습니다.


### 해석 가이드
수업태도
5: 적극적으로 참여하고 질문·발언이 활발해 수업 흐름에 긍정적으로 기여함.
4: 대체로 성실히 참여하며 가끔 산만해져도 스스로 집중을 회복함.
3: 기본 참여 의지는 있으나 발언·질문이 적어 교사의 유도가 필요함.
2: 집중 시간이 짧고 참여도가 낮아 지속적인 관찰과 지도가 필요함.
1: 참여 의지와 집중이 매우 낮아 목표 달성을 위해 강한 개입이 필요함.

수업이해도
5: 내용을 깊이 이해하며 응용·확장 문제도 스스로 해결 가능함.
4: 핵심을 잘 이해하고 간단한 응용 문제는 무리 없이 해결함.
3: 기본 개념은 이해하나 복잡·응용 단계에서 도움이 필요함.
2: 핵심 개념 이해에 어려움이 있어 반복 설명과 보충 자료가 필요함.
1: 기초 개념부터 재학습이 필요함.

과제평가
5: 과제를 성실히 수행하고 정확도·완성도가 높으며 기한을 준수함.
4: 대부분 수행했으나 일부 실수나 누락이 있음.
3: 절반 이상 수행했지만 정확성과 완성도가 부족함.
2: 일부만 수행하거나 기한을 자주 넘김.
1: 거의 수행하지 않거나 미제출함.

질문난이도
5: 매우 심화되고 창의적인 질문으로 학습을 확장함.
4: 심화·응용 수준의 질문을 자주 함.
3: 기본 개념 확인 중심의 질문을 함.
2: 단순 확인 또는 이해 부족에서 비롯된 질문이 많음.
1: 질문이 거의 없거나 수업과 무관한 질문을 함.

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


# ----- 예시 실행 -----
if __name__ == "__main__":
    graph = build_graph()
    example_state = {"student_data": data}  # data 변수를 student_data로 전달
    out = graph.invoke(example_state)
    print(out["numeric_trend"])  # 구조화 결과
    print(out["numeric_trend_text"])  # LLM가 만든 문장
