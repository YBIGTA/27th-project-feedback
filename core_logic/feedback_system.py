# feedback_system.py
import pandas as pd
import os
from typing import Dict, List, Any
from langchain_upstage import ChatUpstage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
load_dotenv()

class FeedbackSystem:
    def __init__(self, model: str = "solar-pro2", temperature: float = 0.3):
        api_key = os.getenv("UPSTAGE_API_KEY")
        if not api_key:
            raise RuntimeError("UPSTAGE_API_KEY 환경변수가 필요합니다.")
        self.llm = ChatUpstage(model=model, temperature=temperature, api_key=api_key)
        self.output_parser = StrOutputParser()

    def calculate_score_changes(self, past_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """전회차 대비 점수 변화 계산"""
        if len(past_records) < 2:
            return {"error": "비교를 위해 최소 2회 수업 데이터가 필요합니다."}

        # 최근 2회 수업 데이터
        latest = past_records[-1]
        previous = past_records[-2]

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
                current = int(latest.get(col, 0))
                prev = int(previous.get(col, 0))
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

        return {"changes": changes, "latest_data": latest, "previous_data": previous}



    def generate_feedback(
        self,
        student_info: Dict[str, Any],
        current_class_info: Dict[str, Any],
        past_records: List[Dict[str, Any]]
        ) -> str:
        """Upstage API를 사용하여 피드백 생성"""
        is_new = len(past_records) < 1

        try:
            system_msg = "너는 경험 많은 수학 과외 선생님입니다."
            if is_new:
                system_msg += "신규 학생의 첫 수업 평가 데이터를 바탕으로 학부모님께 전달할 수 있는 전문적이고 따뜻한 피드백을 작성합니다."
            else:
                system_msg += "교수자가 입력한 수업 평가 데이터와 학생의 이전 수업 기록을 참고하여 피드백을 담은 레포트를 제공해야합니다."
            

            system_msg += """
            **중요**: 이 피드백은 학부모님께 전달되는 것이므로, 
            - 존댓말을 사용하고 정중한 어조로 작성
            - 학부모님이 이해하기 쉽게 명확하게 설명
            - 학생의 첫인상과 학습 태도를 잘 반영
            - 구체적이고 실용적인 조언 제공
            - 마크다운 문법 없이 텍스트로 작성"""

            user_msg = f"""
            [학생 정보]
            - 학생: {student_info.get("name")}
            - 학년: {student_info.get("grade")}"""

            if is_new:
                user_msg += f"""

            [첫 수업 평가 점수]
            - 수업태도: {current_class_info.get("attitude_score")}점
            - 수업이해도: {current_class_info.get("understanding_score")}점
            - 과제평가: {current_class_info.get("homework_score")}점
            - 질문상호작용: {current_class_info.get("qa_score")}점

            [첫 수업 내용]
            {current_class_info.get("progress_text")}

            [첫 수업 특이사항]
            {current_class_info.get("class_memo") if str(current_class_info.get("class_memo", "")).strip() else "특별한 특이사항 없음"}"""
            

            else:
                # 프롬프트 구성 (기존 데이터 참고 포함)
                all_records = past_records + [current_class_info]
                changes_data = self.calculate_score_changes(all_records)
                if "error" in changes_data:
                    return changes_data["error"]

                past_summary = "\n".join([
                    f"- {record.get('date', record.get('class_date'))}: 태도{record['attitude_score']}점, 이해도{record['understanding_score']}점, 과제{record['homework_score']}점, 질문{record['qa_score']}점"
                    for record in all_records[-3:] # 최근 3회 기록
                ])

                user_msg += f"""
[학생 정보]
- 학생: {student_info.get("name")}

[현재 수업 평가 점수]
- 수업태도: {changes_data['changes']['attitude_score']['current']}점
- 수업이해도: {changes_data['changes']['understanding_score']['current']}점
- 과제평가: {changes_data['changes']['homework_score']['current']}점
- 질문상호작용: {changes_data['changes']['qa_score']['current']}점

[현재 수업 내용]
{changes_data['latest_data'].get('progress_text', 'N/A')}

[현재 특이사항]
{changes_data['latest_data'].get('class_memo', 'N/A')}

[이전 수업 기록 (참고용)]
{past_summary}"""


        except Exception as e:
            return f"프롬포트 생성 중 오류 발생: {e}"
        
        try:
            # AI 모델 호출
            user_msg_1 = user_msg + """
            위 정보를 바탕으로 반드시 다음 피드백을 작성해주세요:

            **1. 수업보완: 부족한 부분과 개선 방향**
            [부족한 부분과 개선 방향을 3-5문장으로 작성]

            **중요**: 
            - 점수는 언급하지 말고, 학생의 행동과 태도를 집중하여 작성
            - 학생명은 반드시 실제 이름으로 표시 (S1001 같은 ID 사용 금지)
            - 학부모님이 학생의 학습 상황을 종합적으로 파악할 수 있도록 작성
            - 영역을 구분하지 않고 자연스럽게 작성"""
            response_section1 = self.llm.invoke([("system", system_msg), ("user", user_msg_1)])
            response_section1 = response_section1.content if hasattr(response_section1, "content") else str(response_section1)
        
        except Exception as e:
            return f"피드백 생성 중 오류 발생: {e}"
        
        try:
            user_msg_2 = user_msg + """
            위 정보를 바탕으로 반드시 다음 피드백을 작성해주세요:
            
            **2. 수업태도: 참여도와 학습 자세 평가**
            [참여도와 학습 자세를 3-5문장으로 한 문단으로 작성]
            
            **중요**: 
            - 점수는 언급하지 말고, 학생의 행동과 태도를 집중하여 작성
            - 학생명은 반드시 실제 이름으로 표시 (S1001 같은 ID 사용 금지)
            - 학부모님이 학생의 학습 상황을 종합적으로 파악할 수 있도록 작성
            - 영역을 구분하지 않고 자연스럽게 작성"""
            response_section2 = self.llm.invoke([("system", system_msg), ("user", user_msg_2)])
            response_section2 = response_section2.content if hasattr(response_section2, "content") else str(response_section2)

        except Exception as e:
            return f"피드백 생성 중 오류 발생: {e}"
        try:
            user_msg_3 = user_msg + """
            위 정보를 바탕으로 반드시 다음 피드백을 작성해주세요:

            **3. 전체 Comment: 종합적 평가와 향후 방향**
            [오늘 수업에서 보인 모습과 이전 수업들과의 비교를 자연스럽게 연결하여 종합적으로 평가하고, 향후 방향을 제시 (4-6문장)]

            **중요**: 
            - 점수는 언급하지 말고, 학생의 행동과 태도를 집중하여 작성
            - 학생명은 반드시 실제 이름으로 표시 (S1001 같은 ID 사용 금지)
            - 학부모님이 학생의 학습 상황을 종합적으로 파악할 수 있도록 작성
            - 전체 Comment의 2파트는 자연스럽게 연결되어야 함
            - 2파트에서는 구체적인 변화점과 추세를 언급
            - 학부모님이 학생의 학습 상황을 종합적으로 파악할 수 있도록 작성
            """
            response_section3 = self.llm.invoke([("system", system_msg), ("user", user_msg_3)])
            response_section3 = response_section3.content if hasattr(response_section3, "content") else str(response_section3)
            return response_section1 + "\n\n" + response_section2 + "\n\n" + response_section3
        except Exception as e:
            return f"피드백 생성 중 오류 발생: {e}"

# CSV 데이터 어댑터 및 실행기
class CSVDataProvider:
    """
    CSV 파일을 읽고 Pandas로 전처리한 뒤,
    FeedbackAnalyzer가 사용할 수 있는 표준 형식(딕셔너리)으로 변환합니다.
    """
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

    def get_student_data(self, student_id: str) -> (Dict, Dict, List[Dict]):
        if self.df is None:
            return None, None, None
            
        student_df = self.df[self.df["student_id"] == student_id].sort_values("date")
        if student_df.empty:
            raise ValueError(f"학생 ID '{student_id}'를 CSV에서 찾을 수 없습니다.")

        all_records = student_df.to_dict('records')
        
        student_info = {"name": all_records[-1]['student_name'], "grade": all_records[-1]['grade']}
        current_class_info = all_records[-1]
        past_records = all_records[:-1]
        
        return student_info, current_class_info, past_records

# 테스트 실행
if __name__ == "__main__":
    print("=== 피드백 시스템 테스트 ===")

    # 시스템 초기화
    provider = CSVDataProvider()

    if provider.df is not None:
        # 학생 목록 출력
        students = provider.get_student_list()
        print(f"\n📚 학생 목록: {students}")

        # 첫 번째 학생 테스트
        if students:
            test_student_id = provider.df["student_id"].unique()[0]
            print(f"\n🔍 학생 {test_student_id} 분석 중...")

            # CSV에서 표준 형식으로 데이터 변환
            student_info, current_class, past_records = provider.get_student_data(test_student_id)

            # 피드백 생성 클래스 초기화
            analyzer = FeedbackSystem()
            
            # 점수 변화 계산 및 출력
            all_records = past_records + [current_class]
            if len(all_records) >= 2:
                changes = analyzer.calculate_score_changes(all_records)
                if "error" not in changes:
                    print(f"\n📊 점수 변화:")
                    for col, data in changes["changes"].items():
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
                else:
                    print(f"❌ 오류: {changes['error']}")
                
            # 피드백 생성
            print(f"\n📝 피드백 생성 중...")
            feedback_result = analyzer.generate_feedback(student_info, current_class, past_records)
            
            # 5. 결과 출력
            print("\n--- AI 생성 피드백 ---")
            print(f"\n{feedback_result}")
            print("--------------------")
