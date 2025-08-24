import streamlit as st
import requests
from datetime import date

# --- API 기본 설정 ---
BASE_URL = "http://127.0.0.1:8000"

# --- API 요청 헬퍼 클래스 ---
class ApiClient:
    def __init__(self):
        self.base_url = BASE_URL
        # 세션 상태에서 토큰을 가져옵니다. 없으면 None입니다.
        self.token = st.session_state.get("token")
        self.headers = {
            "Authorization": f"Bearer {self.token}"
        } if self.token else {}

    def _request(self, method, endpoint, **kwargs):
        """공통 요청 로직"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()  # 2xx 상태 코드가 아니면 예외 발생
            # DELETE 요청 등 내용이 없는 성공 응답 처리
            if response.status_code == 204:
                return None
            return response.json()
        except requests.exceptions.HTTPError as err:
            try:
                error_detail = err.response.json()
                detail_message = error_detail.get('detail', '오류 발생')
            except requests.exceptions.JSONDecodeError:
                detail_message = err.response.text
        except requests.exceptions.RequestException as err:
            st.error(f"연결 오류: FastAPI 서버가 실행 중인지 확인하세요. ({err})")
            return None

    # --- 인증 API ---
    def signup(self, email, password, name):
        return self._request("post", "/api/v1/teachers/", json={"email": email, "password": password, "name": name})

    def login(self, email, password):
        # 로그인은 form-data 형식으로 요청합니다.
        return self._request("post", "/api/v1/auth/token", data={"username": email, "password": password})

    # --- 학생 API ---
    def get_students(self):
        return self._request("get", "/api/v1/students")

    def create_student(self, name, grade_id):
        return self._request("post", "/api/v1/students", json={"name": name, "grade_id": grade_id})

    def update_student(self, student_id, name, grade_id):
        return self._request("put", f"/api/v1/students/{student_id}", json={"name": name, "grade_id": grade_id})
    
    def delete_student(self, student_id):
        return self._request("delete", f"/api/v1/students/{student_id}")

    # --- 피드백 API ---
    def get_feedbacks(self, student_id):
        return self._request("get", f"/api/v1/students/{student_id}/feedbacks")

    def create_feedback(self, student_id, class_info, feedback_info):
        payload = {"class_info": class_info, "feedback_info": feedback_info}
        return self._request("post", f"/api/v1/students/{student_id}/feedbacks", json=payload)
    
    # --- 학년 API ---
    def get_grades(self):
        return self._request("get", "/api/v1/grades")

# --- UI 렌더링 함수 ---

def show_login_signup():
    """로그인 및 회원가입 UI를 표시하는 함수"""
    st.title("AI 피드백 시스템")

    login_tab, signup_tab = st.tabs(["로그인", "회원가입"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("이메일")
            password = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인")
            if submitted:
                client = ApiClient()
                response = client.login(email, password)
                if response and "access_token" in response:
                    # 로그인 성공 시 토큰을 세션에 저장하고 페이지를 새로고침합니다.
                    st.session_state["token"] = response["access_token"]
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("로그인에 실패했습니다. 이메일과 비밀번호를 확인하세요.")

    with signup_tab:
        with st.form("signup_form"):
            name = st.text_input("이름")
            email = st.text_input("사용할 이메일")
            password = st.text_input("사용할 비밀번호", type="password")
            submitted = st.form_submit_button("회원가입")
            if submitted:
                client = ApiClient()
                response = client.signup(email, password, name)
                if response:
                    st.success("회원가입 성공! 로그인 탭에서 로그인해주세요.")
                # API 클라이언트에서 이미 에러를 처리하므로 별도 else 불필요

def show_student_management():
    """학생 관리 메인 페이지를 표시하는 함수"""
    client = ApiClient()
    st.sidebar.title(f"안녕하세요!")
    if st.sidebar.button("로그아웃"):
        # 세션 상태를 초기화하고 페이지를 새로고침합니다.
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.title("학생 관리")

    # --- 신규 학생 추가 ---
    with st.expander("신규 학생 추가하기"):
        # API를 통해 전체 학년 목록을 가져옵니다.
        grades_list = client.get_grades()
        if grades_list:
            grade_options = {grade['grade_name']: grade['grade_id'] for grade in grades_list}

            with st.form("new_student_form", clear_on_submit=True):
                name = st.text_input("학생 이름")
                # 숫자 입력 대신 선택 상자 사용
                selected_grade_name = st.selectbox("학년", options=grade_options.keys())
                
                submitted = st.form_submit_button("추가")
                if submitted:
                    # 선택된 학년 이름에 해당하는 ID를 찾아 API로 전송
                    selected_grade_id = grade_options[selected_grade_name]
                    response = client.create_student(name, selected_grade_id) # grade -> grade_id
                    if response:
                        st.toast(f"✅ {name} 학생을 추가했습니다.")
                        st.rerun()

    st.divider()

    # --- 학생 목록 표시 ---
    students = client.get_students()
    if students is None:
        st.warning("학생 정보를 불러오는 데 실패했습니다.")
        return
    if not students:
        st.info("등록된 학생이 없습니다. 먼저 학생을 추가해주세요.")
    else:
        for student in students:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"{student['name']} ({student['grade_info']['grade_name']})")
                
                with col2:
                    # 선택된 학생 ID를 세션에 저장하여 피드백 관리 UI를 표시
                    if st.button("피드백 관리", key=f"manage_{student['student_id']}"):
                        st.session_state["selected_student_id"] = student["student_id"]
                        st.session_state["page"] = "feedback"
                        st.rerun()

                # --- 학생 정보 수정 및 삭제 ---
                with st.expander("학생 정보 수정/삭제"):
                    with st.form(f"edit_form_{student['student_id']}"):
                        new_name = st.text_input("이름", value=student['name'], key=f"name_{student['student_id']}")

                        current_grade_name = student['grade_info']['grade_name']
                        current_grade_index = list(grade_options.keys()).index(current_grade_name) if current_grade_name in grade_options.keys() else 0
                        
                        selected_new_grade_name = st.selectbox("학년", options=grade_options.keys(), index=current_grade_index, key=f"grade_{student['student_id']}")
                        
                        update_col, delete_col = st.columns(2)
                        if update_col.form_submit_button("수정"):
                            selected_new_grade_id = grade_options[selected_new_grade_name]
                            client.update_student(student['student_id'], new_name, selected_new_grade_id)
                            st.toast(f"✅ {new_name} 학생 정보를 수정했습니다.")
                            st.rerun()
                        
                        if delete_col.form_submit_button("삭제"):
                            client.delete_student(student['student_id'])
                            st.toast(f"✅ {student['name']} 학생을 삭제했습니다.")
                            st.rerun()


def show_feedback_management():
    """특정 학생의 피드백 관리 페이지를 표시하는 함수"""
    client = ApiClient()
    student_id = st.session_state.get("selected_student_id")

    if not student_id:
        st.warning("학생이 선택되지 않았습니다. 학생 관리 페이지로 돌아갑니다.")
        st.session_state["page"] = "students"
        st.rerun()
    
    # 학생 정보를 다시 불러와서 제목에 표시 (이름이 바뀔 수 있으므로)
    students = client.get_students()
    student_name = "학생"
    if students:
        selected_student = next((s for s in students if s['student_id'] == student_id), None)
        if selected_student:
            student_name = selected_student['name']

    st.title(f"'{student_name}' 학생 피드백 관리")

    if st.button("◀ 학생 목록으로 돌아가기"):
        st.session_state["page"] = "students"
        del st.session_state["selected_student_id"]
        st.rerun()

    # --- 신규 피드백 생성 ---
    with st.expander("신규 피드백 생성하기"):
        with st.form("new_feedback_form", clear_on_submit=True):
            st.subheader("수업 정보")
            subject = st.text_input("과목")
            class_date = st.date_input("수업 날짜", value=date.today())
            progress_text = st.text_area("수업 진도")
            class_memo = st.text_area("수업 메모")

            st.subheader("평가 점수")
            attitude_score = st.slider("수업 태도", 1, 5, 3)
            understanding_score = st.slider("이해도", 1, 5, 3)
            homework_score = st.slider("과제 수행도", 1, 5, 3)
            qa_score = st.slider("질의응답", 1, 5, 3)

            submitted = st.form_submit_button("AI 피드백 생성")
            if submitted:
                with st.spinner("AI가 피드백을 생성 중입니다..."):
                    class_info = {
                        "subject": subject, "class_date": str(class_date),
                        "progress_text": progress_text, "class_memo": class_memo
                    }
                    feedback_info = {
                        "attitude_score": attitude_score, "understanding_score": understanding_score,
                        "homework_score": homework_score, "qa_score": qa_score
                    }
                    response = client.create_feedback(student_id, class_info, feedback_info)
                if response:
                    st.toast("✅ AI 피드백 생성을 완료했습니다.")
                    st.rerun()

    st.divider()

    # --- 피드백 목록 표시 ---
    st.header("피드백 기록")
    feedbacks = client.get_feedbacks(student_id)
    if feedbacks is None:
        st.warning("피드백 정보를 불러오는 데 실패했습니다.")
        return
    if not feedbacks:
        st.info("작성된 피드백이 없습니다.")
    else:
        for fb in feedbacks:
            # 피드백이 연결된 수업 정보를 찾기 위해 전체 학생 목록을 다시 조회 (비효율적이지만 간단한 구현)
            class_date_str = "날짜 정보 없음"
            if students:
                for s in students:
                    for c in s.get('classes', []):
                        if c.get('feedback') and c['feedback']['feedback_id'] == fb['feedback_id']:
                            class_date_str = c['class_date']
                            break
            
            with st.expander(f"{class_date_str} 수업 피드백"):
                st.markdown(f"**👍 발전한 점**")
                st.info(fb.get('ai_comment_improvement') or "내용 없음")
                st.markdown(f"**💪 개선할 점**")
                st.warning(fb.get('ai_comment_attitude') or "내용 없음")
                st.markdown(f"**📝 총평**")
                st.success(fb.get('ai_comment_overall') or "내용 없음")


# --- 메인 앱 로직 ---
def main():
    """메인 함수: 세션 상태에 따라 적절한 페이지를 보여줍니다."""
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        show_login_signup()
    else:
        # 페이지 상태가 없으면 학생 관리 페이지를 기본으로 설정
        if "page" not in st.session_state:
            st.session_state["page"] = "students"

        if st.session_state["page"] == "students":
            show_student_management()
        elif st.session_state["page"] == "feedback":
            show_feedback_management()

if __name__ == "__main__":
    main()
