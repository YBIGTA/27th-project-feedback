# feedback_system.py
import pandas as pd
import os
from typing import Dict, List, Any
from langchain_upstage import ChatUpstage


class FeedbackSystem:
    def __init__(self, csv_path: str = "data/math_feedback.csv"):
        self.csv_path = csv_path
        self.df = None
        self.load_data()

    def load_data(self):
        """CSV 데이터 로드 및 전처리"""
        try:
            self.df = pd.read_csv(self.csv_path)
            # 날짜 형식이 일관되지 않을 수 있으므로 errors='coerce' 사용
            self.df["date"] = pd.to_datetime(self.df["date"], errors="coerce")
            # 날짜가 파싱되지 않은 행 제거
            self.df = self.df.dropna(subset=["date"])
            self.df = self.df.sort_values(["student_id", "date"])
            print(
                f"✅ 데이터 로드 완료: {len(self.df)}개 행, "
                f"{self.df['student_id'].nunique()}명 학생"
            )
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            self.df = None

    def get_student_list(self) -> List[str]:
        """학생 ID 목록 반환"""
        if self.df is None:
            return []
        return sorted(self.df["student_id"].unique().tolist())

    def find_student_by_name(self, student_name: str) -> str:
        """학생 이름으로 기존 학생 ID 찾기"""
        if self.df is None:
            return None

        # 이름이 정확히 일치하는 학생 찾기
        exact_match = self.df[self.df["student_name"] == student_name]
        if len(exact_match) > 0:
            return exact_match.iloc[0]["student_id"]

        # 부분 일치하는 학생 찾기 (한글 이름의 경우)
        partial_match = self.df[
            self.df["student_name"].str.contains(student_name, na=False)
        ]
        if len(partial_match) > 0:
            # 가장 최근에 수업한 학생 반환
            latest_student = partial_match.sort_values("date").iloc[-1]
            return latest_student["student_id"]

        return None

    def get_student_name_by_id(self, student_id: str) -> str:
        """학생 ID로 학생 이름 가져오기"""
        if self.df is None:
            return student_id

        student_data = self.df[self.df["student_id"] == student_id]
        if len(student_data) > 0:
            return student_data.iloc[0]["student_name"]
        return student_id

    def get_student_trend(self, student_id: str) -> Dict[str, str]:
        """기존 학생의 최근 점수 변화 추세 반환"""
        if self.df is None:
            return {}

        student_data = self.df[self.df["student_id"] == student_id].copy()
        if len(student_data) < 2:
            return {}

        # 최근 3회 수업 데이터
        recent_data = student_data.tail(3)
        trends = {}

        score_columns = {
            "attitude_score": "수업태도",
            "understanding_score": "수업이해도",
            "homework_score": "과제평가",
            "qa_score": "질문상호작용",
        }

        for col, col_name in score_columns.items():
            scores = recent_data[col].tolist()
            if len(scores) >= 2:
                latest = scores[-1]
                previous = scores[-2]

                if latest > previous:
                    trend = f"{previous}점 → {latest}점 ▲"
                elif latest < previous:
                    trend = f"{previous}점 → {latest}점 ▼"
                else:
                    trend = f"{previous}점 → {latest}점 ●"

                trends[col_name] = trend

        return trends

    def add_new_student(
        self,
        student_id: str,
        student_name: str,
        grade: str = "고1",
        subject: str = "수학",
    ) -> bool:
        """신규 학생 추가"""
        try:
            # 이미 존재하는 학생인지 확인
            if student_id in self.df["student_id"].values:
                print(f"⚠️ 학생 ID {student_id}는 이미 존재합니다.")
                return False

            # 새로운 학생 데이터 생성 (오늘 날짜로)
            from datetime import datetime

            today = datetime.now().strftime("%Y-%m-%d")

            new_student_data = {
                "date": today,
                "student_id": student_id,
                "student_name": student_name,
                "grade": grade,
                "subject": subject,
                "attendance": "출석",
                "attitude_score": 3,
                "understanding_score": 3,
                "homework_score": 3,
                "qa_score": 3,
                "progress_text": "신규 학생 첫 수업",
                "absence_reason": "",
                "class_memo": "신규 학생 등록",
                "수업보완": "",
                "수업태도": "",
                "전체수업 Comment": "",
            }

            # 데이터프레임에 추가
            self.df = pd.concat(
                [self.df, pd.DataFrame([new_student_data])], ignore_index=True
            )

            # CSV 파일에 저장
            self.df.to_csv(self.csv_path, index=False)
            print(f"✅ 신규 학생 {student_name}({student_id}) 추가 완료")
            return True

        except Exception as e:
            print(f"❌ 신규 학생 추가 실패: {e}")
            return False

    def is_new_student(self, student_id: str) -> bool:
        """신규 학생 여부 확인 (수업 기록이 1회 이하인 경우)"""
        if self.df is None:
            return False

        student_records = self.df[self.df["student_id"] == student_id]
        return len(student_records) <= 1

    def calculate_score_changes(self, student_id: str) -> Dict[str, Any]:
        """전회차 대비 점수 변화 계산"""
        if self.df is None:
            return {"error": "데이터가 로드되지 않았습니다."}

        student_data = self.df[self.df["student_id"] == student_id].copy()

        if len(student_data) < 2:
            return {"error": "비교를 위해 최소 2회 수업 데이터가 필요합니다."}

        # 최근 2회 수업 데이터
        latest = student_data.iloc[-1]
        previous = student_data.iloc[-2]

        # 점수 변화 계산
        changes = {}
        score_columns = [
            "attitude_score",
            "understanding_score",
            "homework_score",
            "qa_score",
        ]

        for col in score_columns:
            try:
                current = int(latest[col])
                prev = int(previous[col])
                diff = current - prev

                if diff > 0:
                    symbol = "▲"  # 상승
                elif diff < 0:
                    symbol = "▼"  # 하락
                else:
                    symbol = "●"  # 동일

                changes[col] = {
                    "current": current,
                    "previous": prev,
                    "change": diff,
                    "symbol": symbol,
                }
            except (ValueError, TypeError):
                changes[col] = {"error": f"점수 변환 실패"}

        return {
            "student_id": student_id,
            "student_name": latest.get("student_name", "N/A"),
            "latest_date": latest["date"],
            "previous_date": previous["date"],
            "changes": changes,
            "latest_data": latest.to_dict(),
            "previous_data": previous.to_dict(),
        }

    def generate_feedback(self, student_id: str) -> str:
        """Upstage API를 사용하여 피드백 생성"""
        changes = self.calculate_score_changes(student_id)

        if "error" in changes:
            return f"오류: {changes['error']}"

        try:
            llm = self._get_llm()

            # 프롬프트 구성 (기존 데이터 참고 포함)
            system_msg = """너는 경험 많은 수학 과외 선생님입니다. 
            교수자가 입력한 수업 평가 데이터와 학생의 이전 수업 기록을 참고하여 
            피드백을 담은 레포트를 제공해야합니다.
            
            **중요**: 이 피드백은 학부모님께 전달되는 것이므로, 
            - 반드시 3개 섹션으로 구성해야 함
            - 3번째 섹션에 "학습 추세 분석"을 반드시 포함해야 함
            - 존댓말을 사용하고 정중한 어조로 작성
            - 학부모님이 이해하기 쉽게 명확하게 설명
            - 학생의 장점과 개선점을 균형있게 제시
            - 구체적이고 실용적인 조언 제공"""

            user_msg = f"""
[학생 정보]
- 학생: {self.get_student_name_by_id(student_id)}

[현재 수업 평가 점수]
- 수업태도: {changes['changes']['attitude_score']['current']}점
- 수업이해도: {changes['changes']['understanding_score']['current']}점  
- 과제평가: {changes['changes']['homework_score']['current']}점
- 질문상호작용: {changes['changes']['qa_score']['current']}점

[현재 수업 내용]
{changes['latest_data'].get('progress_text', 'N/A')}

[현재 특이사항]
{changes['latest_data'].get('class_memo', 'N/A')}

[이전 수업 기록 (참고용)]
{chr(10).join([f"- {record['date']}: 태도{record['attitude_score']}점, 이해도{record['understanding_score']}점, 과제{record['homework_score']}점, 질문{record['qa_score']}점" for record in self.df[self.df['student_id'] == student_id].tail(3).to_dict('records')])}

위 정보를 바탕으로 다음 3개 섹션으로 구성된 피드백을 작성해주세요:

1. 수업보완: 부족한 부분과 개선 방향 (3-5문장)
2. 수업태도: 참여도와 학습 자세 평가 (3-5문장)  
3. 전체 Comment: 다음 2파트로 구성
   - 1파트: 오늘 수업에서 보인 모습과 평가 (3-4문장)
   - 2파트: 이전 수업들과 비교한 학습 추세 분석 (3-4문장)

**중요**: 
- 전체 Comment의 2파트는 자연스럽게 연결되어야 함
- 2파트에서는 구체적인 변화점과 추세를 언급
- 학부모님이 학생의 학습 상황을 종합적으로 파악할 수 있도록 작성"""

            response = llm.invoke([("system", system_msg), ("user", user_msg)])
            return response.content if hasattr(response, "content") else str(response)

        except Exception as e:
            return f"피드백 생성 중 오류 발생: {e}"

    def generate_feedback_for_new_student(
        self,
        student_id: str,
        attitude: int,
        understanding: int,
        homework: int,
        qa: int,
        progress: str,
        memo: str,
    ) -> str:
        """신규 학생을 위한 피드백 생성 (이전 기록 없이)"""
        try:
            llm = self._get_llm()

            # 학생 정보 가져오기
            student_data = self.df[self.df["student_id"] == student_id]
            if len(student_data) == 0:
                return "오류: 학생 정보를 찾을 수 없습니다."

            student_name = student_data.iloc[0]["student_name"]
            grade = student_data.iloc[0]["grade"]

            # 프롬프트 구성
            system_msg = """너는 경험 많은 수학 과외 선생님입니다. 
            신규 학생의 첫 수업 평가 데이터를 바탕으로 학부모님께 전달할 수 있는 
            전문적이고 따뜻한 피드백을 작성합니다.
            
            **중요**: 이 피드백은 학부모님께 전달되는 것이므로, 
            - 반드시 4개 섹션으로 구성해야 함
            - 4번째 섹션 "학습 추세 분석"을 반드시 포함해야 함
            - 존댓말을 사용하고 정중한 어조로 작성
            - 학부모님이 이해하기 쉽게 명확하게 설명
            - 학생의 첫인상과 학습 태도를 잘 반영
            - 구체적이고 실용적인 조언 제공"""

            user_msg = f"""
[학생 정보]
- 학생: {student_name}
- 학년: {grade}
- 상태: 신규 학생 (첫 수업)

[첫 수업 평가 점수]
- 수업태도: {attitude}점
- 수업이해도: {understanding}점  
- 과제평가: {homework}점
- 질문상호작용: {qa}점

[첫 수업 내용]
{progress}

[첫 수업 특이사항]
{memo if memo.strip() else "특별한 특이사항 없음"}

[이전 수업 기록 (참고용)]
{chr(10).join([f"- {record['date']}: 태도{record['attitude_score']}점, 이해도{record['understanding_score']}점, 과제{record['homework_score']}점, 질문{record['qa_score']}점" for record in self.df[self.df['student_id'] == student_id].tail(3).to_dict('records')])}

위 정보를 바탕으로 반드시 다음 4개 섹션으로 구성된 피드백을 작성해주세요:

**1. 수업보완: 부족한 부분과 개선 방향**
[부족한 부분과 개선 방향을 3-5문장으로 작성]

**2. 수업태도: 참여도와 학습 자세 평가**
[참여도와 학습 자세를 3-5문장으로 작성]

**3. 전체 Comment: 종합적 평가와 향후 방향**
[오늘 수업에서 보인 모습과 이전 수업들과의 비교를 자연스럽게 연결하여 종합적으로 평가하고, 향후 방향을 제시 (4-6문장)]

**중요**: 
- 반드시 4개 섹션 모두 작성해야 함
- 4번째 섹션 "학습 추세 분석"을 반드시 포함해야 함
- 각 섹션은 별도 문단으로 작성하여 구분이 명확해야 함
- 점수는 언급하지 말고, 학생의 행동과 태도를 집중하여 작성
- 학생명은 반드시 실제 이름으로 표시 (S1001 같은 ID 사용 금지)
- 학부모님이 학생의 학습 상황을 종합적으로 파악할 수 있도록 작성"""

            response = llm.invoke([("system", system_msg), ("user", user_msg)])
            return response.content if hasattr(response, "content") else str(response)

        except Exception as e:
            return f"피드백 생성 중 오류 발생: {e}"

    def _get_llm(self, model: str = "solar-pro-250422", temperature: float = 0.3):
        """Upstage LLM 인스턴스 생성"""
        api_key = os.getenv("UPSTAGE_API_KEY")
        if not api_key:
            raise RuntimeError("UPSTAGE_API_KEY 환경변수가 필요합니다.")
        return ChatUpstage(model=model, temperature=temperature, api_key=api_key)


# 테스트 실행
if __name__ == "__main__":
    print("=== 피드백 시스템 테스트 ===")

    # 시스템 초기화
    system = FeedbackSystem()

    if system.df is not None:
        # 학생 목록 출력
        students = system.get_student_list()
        print(f"\n📚 학생 목록: {students}")

        # 첫 번째 학생 테스트
        if students:
            first_student = students[0]
            print(f"\n🔍 학생 {first_student} 분석 중...")

            # 점수 변화 계산
            changes = system.calculate_score_changes(first_student)
            if "error" not in changes:
                print(f"\n📊 점수 변화:")
                for col, data in changes["changes"].items():
                    if "error" not in data:
                        col_name = {
                            "attitude_score": "수업태도",
                            "understanding_score": "수업이해도",
                            "homework_score": "과제평가",
                            "qa_score": "질문상호작용",
                        }[col]

                        print(
                            f"  {col_name}: {data['current']}점 {data['symbol']} "
                            f"(이전: {data['previous']}점)"
                        )

                print(f"\n📝 피드백 생성 중...")
                feedback = system.generate_feedback(first_student)
                print(f"\n{feedback}")
            else:
                print(f"❌ 오류: {changes['error']}")
