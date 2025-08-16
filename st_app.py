import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- 기본 설정 ---
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

st.set_page_config(
    page_title="AI 과외 피드백 시스템",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 AI 과외 피드백 생성 시스템")

# --- API 호출 함수 ---

def get_students():
    """백엔드에서 모든 학생 목록을 가져옵니다."""
    try:
        response = requests.get(f"{API_BASE_URL}/students")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"학생 목록 로딩 실패: {response.status_code}")
            return []
    except requests.exceptions.ConnectionError:
        st.error("백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
        return None

def add_student(name, grade):
    """신규 학생을 백엔드에 추가합니다."""
    student_data = {"name": name, "grade": grade}
    try:
        response = requests.post(f"{API_BASE_URL}/students", json=student_data)
        return response
    except requests.exceptions.ConnectionError:
        return None

def generate_feedback(student_id, class_info, feedback_info):
    """특정 학생의 피드백 생성을 요청합니다."""
    payload = {
        "class_info": class_info,
        "feedback_info": feedback_info
    }
    try:
        response = requests.post(f"{API_BASE_URL}/students/{student_id}/feedbacks", json=payload)
        return response
    except requests.exceptions.ConnectionError:
        return None

# --- 사이드바 ---

st.sidebar.header("학생 관리")

# 학생 목록 조회 및 선택
students = get_students()
if students is not None:
    student_names = {f"{s['name']} (ID: {s['student_id']})": s for s in students}
    selected_student_name = st.sidebar.selectbox(
        "피드백을 생성할 학생을 선택하세요.",
        options=student_names.keys(),
        index=None,
        placeholder="학생 선택..."
    )
    selected_student = student_names.get(selected_student_name)
else:
    selected_student = None

# 신규 학생 추가
with st.sidebar.expander("신규 학생 추가"):
    with st.form("new_student_form", clear_on_submit=True):
        new_name = st.text_input("이름")
        new_grade = st.number_input("학년", min_value=1, max_value=12, step=1)
        submitted = st.form_submit_button("추가")
        if submitted:
            if new_name:
                response = add_student(new_name, new_grade)
                if response and response.status_code == 201:
                    st.success(f"'{new_name}' 학생을 추가했습니다.")
                    st.rerun()
                else:
                    st.error("학생 추가에 실패했습니다.")
            else:
                st.warning("학생 이름을 입력해주세요.")

# --- 메인 화면 ---

if selected_student:
    st.header(f"📝 '{selected_student['name']}' 학생 피드백 생성")

    with st.form("feedback_form"):
        st.subheader("수업 정보")
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("과목", value="수학")
        with col2:
            class_date = st.date_input("수업 날짜", value=datetime.today())
        
        progress_text = st.text_input("수업 진도", placeholder="예: 2단원 분수의 나눗셈")
        class_memo = st.text_area("특이 사항", placeholder="예: 오늘따라 집중력이 좋았음")

        st.divider()

        st.subheader("수업 평가 점수 (1-5점)")
        col1, col2 = st.columns(2)
        with col1:
            attitude_score = st.slider("수업 태도", 1, 5, 3)
            understanding_score = st.slider("수업 이해도", 1, 5, 3)
        with col2:
            qa_score = st.slider("질문/상호작용", 1, 5, 3)
            no_homework = st.checkbox("과제 없음")
            homework_score_value = 99 if no_homework else 3
            homework_score = st.slider("과제 평가", 1, 5, homework_score_value, disabled=no_homework)
            
        # 피드백 생성 버튼
        submit_feedback = st.form_submit_button("🤖 AI 피드백 생성하기", use_container_width=True)

    if submit_feedback:
        with st.spinner("AI가 피드백을 생성 중입니다..."):
            class_info = {
                "subject": subject,
                "class_date": class_date.isoformat(),
                "progress_text": progress_text,
                "class_memo": class_memo
            }
            feedback_info = {
                "attitude_score": attitude_score,
                "understanding_score": understanding_score,
                "homework_score": homework_score,
                "qa_score": qa_score
            }

            response = generate_feedback(selected_student['student_id'], class_info, feedback_info)

            if response and response.status_code == 200:
                feedback_result = response.json().get('feedback', {})
                st.success("AI 피드백 생성이 완료되었습니다!")
                
                st.subheader("✅ AI 생성 피드백 결과")
                st.markdown(f"**수업 보완점**")
                st.info(feedback_result.get('ai_comment_improvement', 'N/A'))
                
                st.markdown(f"**수업 태도**")
                st.info(feedback_result.get('ai_comment_attitude', 'N/A'))

                st.markdown(f"**전체 Comment**")
                st.info(feedback_result.get('ai_comment_overall', 'N/A'))
            else:
                st.error("피드백 생성에 실패했습니다. 백엔드 로그를 확인해주세요.")

else:
    st.info("👈 사이드바에서 학생을 선택하거나 신규 학생을 추가해주세요.")

