from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Teacher(Base):
    """
    선생님(유저) 정보 테이블 모델
    """
    __tablename__ = "teachers"
    
    teacher_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
class Student(Base):
    """
    학생 정보 테이블 모델
    """
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    grade = Column(Integer, nullable=False)

    classes = relationship("Class", back_populates="student", cascade="all, delete-orphan")


class Class(Base):
    """
    수업 기록 테이블 모델
    """
    __tablename__ = "classes"

    class_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"))
    subject = Column(String(50), nullable=False)
    class_date = Column(Date, nullable=False)
    progress_text = Column(String(255))
    class_memo = Column(Text)

    student = relationship("Student", back_populates="classes")
    feedback = relationship("Feedback", back_populates="class_record", uselist=False, cascade="all, delete-orphan")


class Feedback(Base):
    """
    피드백 및 평가 점수 테이블 모델
    """
    __tablename__ = "feedbacks"

    feedback_id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.class_id", ondelete="CASCADE"))
    attitude_score = Column(Integer, nullable=False)
    understanding_score = Column(Integer, nullable=False)
    homework_score = Column(Integer, nullable=False)
    qa_score = Column(Integer, nullable=False)
    ai_comment_improvement = Column(Text)
    ai_comment_attitude = Column(Text)
    ai_comment_overall = Column(Text)
    
    class_record = relationship("Class", back_populates="feedback")
