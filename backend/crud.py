from sqlalchemy.orm import Session, joinedload
from . import models, schemas
from .security import get_password_hash

def get_teacher_by_email(db: Session, email: str):
    """
    이메일로 특정 선생님의 정보를 조회합니다.
    로그인 시 사용자를 확인하는 데 사용됩니다.
    """
    return db.query(models.Teacher).filter(models.Teacher.email == email).first()

def create_teacher(db: Session, teacher: schemas.TeacherCreate):
    """
    새로운 선생님 사용자를 생성합니다.
    입력받은 비밀번호를 해싱하여 저장합니다.
    """
    hashed_password = get_password_hash(teacher.password)
    db_teacher = models.Teacher(
        email=teacher.email,
        name=teacher.name,
        hashed_password=hashed_password
    )
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

def get_student(db: Session, student_id: int):
    """
    ID로 특정 학생 한 명의 정보를 조회
    """
    return db.query(models.Student).filter(models.Student.student_id == student_id).first()

def get_students(db: Session, skip: int = 0, limit: int = 100):
    """
    모든 학생의 정보를 조회
    """
    return db.query(models.Student).offset(skip).limit(limit).all()

def create_student(db: Session, student: schemas.StudentCreate):
    """
    새로운 학생 정보 생성
    """
    db_student = models.Student(name=student.name, grade=student.grade)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def update_student(db: Session, student_id: int, student_update: schemas.StudentUpdate):
    """
    기존 학생 정보 수정
    """
    db_student = get_student(db, student_id)
    if db_student:
        update_data = student_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_student, key, value)
        db.commit()
        db.refresh(db_student)
    return db_student

def delete_student(db: Session, student_id: int):
    """
    특정 학생 정보 삭제
    """
    db_student = get_student(db, student_id)
    if db_student:
        db.delete(db_student)
        db.commit()
    return db_student

def get_student_past_classes(db: Session, student_id: int, limit: int = 5):
    """
    특정 학생의 과거 수업 기록을 최근 순서로 조회
    AI 피드백 생성을 위해 이전 기록을 참조할 때 사용할 수 있음
    """
    return db.query(models.Class)\
        .filter(models.Class.student_id == student_id)\
        .options(joinedload(models.Class.feedback))\
        .order_by(models.Class.class_date.desc())\
        .limit(limit)\
        .all()

def create_class_and_feedback(db: Session, student_id: int, class_info: schemas.ClassCreate, feedback_info: schemas.FeedbackCreate):
    """
    수업 기록 및 피드백 생성
    """
    # 수업 기록(Class) 생성
    db_class = models.Class(
        student_id=student_id,
        **class_info.dict()
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)

    # 피드백(Feedback) 생성
    db_feedback = models.Feedback(
        class_id=db_class.class_id,
        **feedback_info.dict()
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    return db_class

def update_feedback_with_ai_comment(db: Session, feedback_id: int, ai_comments: dict):
    """
    AI가 생성한 코멘트를 기존 피드백 레코드에 업데이트
    """
    db_feedback = db.query(models.Feedback).filter(models.Feedback.feedback_id == feedback_id).first()
    if db_feedback:
        db_feedback.ai_comment_improvement = ai_comments.get("improvement")
        db_feedback.ai_comment_attitude = ai_comments.get("attitude")
        db_feedback.ai_comment_overall = ai_comments.get("overall")
        db.commit()
        db.refresh(db_feedback)
    return db_feedback

def get_feedback(db: Session, feedback_id: int):
    """
    ID로 특정 피드백 한 개 조회
    """
    return db.query(models.Feedback).filter(models.Feedback.feedback_id == feedback_id).first()

def get_feedbacks_by_student(db: Session, student_id: int):
    """
    특정 학생의 모든 피드백 조회
    """
    return db.query(models.Feedback)\
        .join(models.Class)\
        .filter(models.Class.student_id == student_id)\
        .order_by(models.Class.class_date.desc())\
        .all()

def update_feedback(db: Session, feedback_id: int, feedback_update: schemas.FeedbackUpdate):
    """
    기존 피드백 수정
    """
    db_feedback = get_feedback(db, feedback_id)
    if db_feedback:
        update_data = feedback_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_feedback, key, value)
        db.commit()
        db.refresh(db_feedback)
    return db_feedback