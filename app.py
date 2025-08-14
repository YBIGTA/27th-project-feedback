# app.py - 터미널 전용 버전
from feedback_system import FeedbackSystem
from dotenv import load_dotenv


# 환경변수 로드
load_dotenv()


def main():
    print("📚 과외 피드백 자동 생성 시스템")
    print("=" * 50)
    
    try:
        # 피드백 시스템 초기화
        system = FeedbackSystem()
        
        if system.df is None:
            print("❌ 학생 데이터를 불러올 수 없습니다.")
            return
        
        print(f"✅ 데이터 로드 완료: {len(system.df)}개 행, "
              f"{system.df['student_id'].nunique()}명 학생")
        print()
        
        # 학생 이름 입력
        while True:
            student_name = input("학생 이름을 입력하세요: ").strip()
            if student_name:
                break
            print("❌ 학생 이름을 입력해주세요.")
        
        # 기존 학생인지 확인
        existing_student = system.find_student_by_name(student_name)
        
        if existing_student:
            print(f"\n👤 기존 학생 발견: {student_name}")
            selected_student = existing_student
            
            # 기존 학생의 점수 변화 추세 표시
            print("\n📊 최근 수업 점수 변화:")
            trend_info = system.get_student_trend(existing_student)
            if trend_info:
                for score_type, trend in trend_info.items():
                    print(f"  {score_type}: {trend}")
            print()
            
            # 최신 수업 데이터로 추세 업데이트
            latest_data = system.df[system.df['student_id'] == existing_student].iloc[-1]
            print(f"📅 최근 수업일: {latest_data['date'].strftime('%Y-%m-%d')}")
            print(f"📚 최근 수업 내용: {latest_data['progress_text']}")
            print()
        else:
            print(f"\n🆕 신규 학생: {student_name}")
            # 신규 학생 추가
            selected_student = add_new_student(system, student_name)
            if not selected_student:
                print("❌ 신규 학생 추가가 취소되었습니다.")
                return
        
        # 학생 이름으로 표시
        student_display_name = system.get_student_name_by_id(selected_student)
        print(f"\n👤 선택된 학생: {student_display_name}")
        print("-" * 50)
        
        # 수업 평가 점수 입력
        print("\n🎯 수업 평가 점수 입력 (1-5점, 과제 없을 경우 99)")
        print()
        
        while True:
            try:
                attitude_score = int(input("수업태도 (참여도 및 집중력): "))
                if 1 <= attitude_score <= 5:
                    break
                print("❌ 1-5점 사이의 점수를 입력해주세요.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
        
        while True:
            try:
                understanding_score = int(input("수업이해도: "))
                if 1 <= understanding_score <= 5:
                    break
                print("❌ 1-5점 사이의 점수를 입력해주세요.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
        
        while True:
            try:
                homework_score = int(input("과제평가 (과제 없을 경우 99): "))
                if homework_score == 99 or (1 <= homework_score <= 5):
                    break
                print("❌ 1-5점 또는 99를 입력해주세요.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
        
        while True:
            try:
                qa_score = int(input("질문상호작용: "))
                if 1 <= qa_score <= 5:
                    break
                print("❌ 1-5점 사이의 점수를 입력해주세요.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
        
        print()
        progress_text = input("📖 수업 진도: ")
        class_memo = input("💬 특이사항: ")
        
        print("\n" + "=" * 50)
        print("🚀 AI 피드백 생성 중...")
        print("=" * 50)
        
        # AI 피드백 생성
        if system.is_new_student(selected_student):
            # 신규 학생용 피드백 생성
            feedback = system.generate_feedback_for_new_student(
                selected_student, attitude_score, understanding_score,
                homework_score, qa_score, progress_text, class_memo
            )
        else:
            # 기존 학생용 피드백 생성
            feedback = generate_feedback_with_context(
                system, selected_student, attitude_score, understanding_score,
                homework_score, qa_score, progress_text, class_memo
            )
        
        # 피드백 생성 결과 표시
        if feedback and "오류" not in feedback and "피드백 생성 중 오류" not in feedback:
            print("\n🤖 AI 생성 피드백")
            print("-" * 50)
            print(feedback)
            print("-" * 50)
            
            # 점수 변화 요약 표시
            print("\n📊 이번 수업 점수 요약:")
            print(f"  수업태도: {attitude_score}점")
            print(f"  수업이해도: {understanding_score}점")
            print(f"  과제평가: {homework_score}점")
            print(f"  질문상호작용: {qa_score}점")
            
            # 기존 학생인 경우 변화 표시 (방금 입력한 데이터 vs 이전 수업)
            if not system.is_new_student(selected_student):
                print("\n📈 이전 수업 대비 변화:")
                # 방금 입력한 데이터와 이전 수업 비교
                current_scores = {
                    'attitude_score': attitude_score,
                    'understanding_score': understanding_score,
                    'homework_score': homework_score,
                    'qa_score': qa_score
                }
                
                # 이전 수업 데이터 가져오기
                student_data = system.df[system.df['student_id'] == selected_student]
                if len(student_data) >= 2:
                    previous_scores = student_data.iloc[-2]  # 직전 수업
                    
                    score_names = {
                        'attitude_score': '수업태도',
                        'understanding_score': '수업이해도',
                        'homework_score': '과제평가',
                        'qa_score': '질문상호작용'
                    }
                    
                    for col, col_name in score_names.items():
                        current = current_scores[col]
                        previous = previous_scores[col]
                        
                        if current > previous:
                            trend = f"{previous}점 → {current}점 ▲"
                        elif current < previous:
                            trend = f"{previous}점 → {current}점 ▼"
                        else:
                            trend = f"{previous}점 → {current}점 ●"
                        
                        print(f"  {col_name}: {trend}")
                else:
                    print("  이전 수업 기록이 부족하여 변화를 분석할 수 없습니다.")
            else:
                print("\n🆕 신규 학생 첫 수업입니다.")
        else:
            print(f"❌ 피드백 생성 실패: {feedback}")
            
    except Exception as e:
        print(f"❌ 시스템 오류: {e}")


def add_new_student(system, student_name):
    """신규 학생 추가 함수"""
    print("\n🆕 신규 학생 추가")
    print("-" * 30)
    
    try:
        # 학생 ID 자동 생성 (S + 4자리 숫자)
        existing_ids = system.df['student_id'].tolist()
        next_id = 1
        while f"S{next_id:04d}" in existing_ids:
            next_id += 1
        student_id = f"S{next_id:04d}"
        
        grade = input("학년 (기본값: 고1): ").strip()
        if not grade:
            grade = "고1"
        
        subject = input("과목 (기본값: 수학): ").strip()
        if not subject:
            subject = "수학"
        
        print("\n📝 입력된 정보:")
        print(f"  학생 ID: {student_id}")
        print(f"  학생 이름: {student_name}")
        print(f"  학년: {grade}")
        print(f"  과목: {subject}")
        
        confirm = input("\n위 정보로 신규 학생을 추가하시겠습니까? (y/N): ").strip().lower()
        if confirm in ['y', 'yes', '예']:
            if system.add_new_student(student_id, student_name, grade, subject):
                return student_id
            else:
                return None
        else:
            print("❌ 신규 학생 추가가 취소되었습니다.")
            return None
            
    except Exception as e:
        print(f"❌ 신규 학생 추가 중 오류 발생: {e}")
        return None


def generate_feedback_with_context(system, student_id, attitude, understanding, 
                                 homework, qa, progress, memo):
    """입력된 데이터와 기존 데이터를 참고하여 피드백 생성"""
    try:
        llm = system._get_llm()
        
        # 선택된 학생의 이전 수업 기록 가져오기 (참고 정보)
        student_data = system.df[system.df['student_id'] == student_id].tail(3)
        previous_records = []
        
        for _, row in student_data.iterrows():
            previous_records.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'attitude': row['attitude_score'],
                'understanding': row['understanding_score'],
                'homework': row['homework_score'],
                'qa': row['qa_score'],
                'progress': row.get('progress_text', 'N/A'),
                'memo': row.get('class_memo', 'N/A')
            })
        
        # 프롬프트 구성 (기존 데이터 참고 포함)
        system_msg = """너는 경험 많은 수학 과외 선생님입니다. 
        교수자가 입력한 수업 평가 데이터와 학생의 이전 수업 기록을 참고하여 
        학부모에게 전달할 수 있는 전문적이고 따뜻한 피드백을 작성합니다."""
        
        user_msg = f"""
[학생 정보]
- 학생: {system.get_student_name_by_id(student_id)}

[현재 수업 평가 점수]
- 수업태도: {attitude}점
- 수업이해도: {understanding}점  
- 과제평가: {homework}점
- 질문상호작용: {qa}점

[현재 수업 내용]
{progress}

[현재 특이사항]
{memo if memo.strip() else "특별한 특이사항 없음"}

[이전 수업 기록 (참고용)]
{chr(10).join([f"- {record['date']}: 태도{record['attitude']}점, 이해도{record['understanding']}점, 과제{record['homework']}점, 질문{record['qa']}점" for record in previous_records])}

위 정보를 바탕으로 다음 3개 섹션으로 구성된 피드백을 작성해주세요:

1. 수업보완: 부족한 부분과 개선 방향 (3-5문장)
2. 수업태도: 참여도와 학습 자세 평가 (3-5문장)  
3. 전체 Comment: 종합적 평가와 향후 방향 (3-5문장)

**중요**: 
- 반드시 "{system.get_student_name_by_id(student_id)}"라는 학생 이름을 사용하여 작성
- S1001, S1002 같은 학생 ID는 절대 사용하지 말 것
- 이전 수업 기록을 참고하여 학생의 변화나 지속적인 패턴을 반영
- 각 섹션은 3-5문장으로 작성하고, 점수는 언급하지 말고 학생의 행동과 태도에 집중
- 학부모님께 전달할 수 있는 형태로 작성
"""
        
        response = llm.invoke([("system", system_msg), ("user", user_msg)])
        return response.content if hasattr(response, "content") else str(response)
        
    except Exception as e:
        return f"피드백 생성 중 오류 발생: {e}"


if __name__ == "__main__":
    main()
