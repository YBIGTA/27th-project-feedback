from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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
    created_at = Column(DateTime, server_default=func.now())
    # Teacher -> Student (One-to-Many)
    students = relationship("Student", back_populates="teacher", cascade="all, delete-orphan")
    # Teacher -> Class (One-to-Many)
    classes = relationship("Class", back_populates="teacher", cascade="all, delete-orphan")


class Student(Base):
    """
    학생 정보 테이블 모델
    """
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    grade = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Student -> Teacher (Many-to-One)
    teacher = relationship("Teacher", back_populates="students")
    # Student -> Class (One-to-Many)
    classes = relationship("Class", back_populates="student", cascade="all, delete-orphan")


class Class(Base):
    """
    수업 기록 테이블 모델
    """
    __tablename__ = "classes"

    class_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(50), nullable=False)
    class_date = Column(Date, nullable=False)
    progress_text = Column(String(255))
    class_memo = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    # Class -> Student (Many-to-One)
    student = relationship("Student", back_populates="classes")
    # Class -> Teacher (Many-to-One)
    teacher = relationship("Teacher", back_populates="classes")
    # Class -> Feedback (One-to-One)
    feedback = relationship("Feedback", back_populates="class_record", uselist=False, cascade="all, delete-orphan")


class Feedback(Base):
    """
    피드백 및 평가 점수 테이블 모델
    """
    __tablename__ = "feedbacks"

    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("classes.class_id", ondelete="CASCADE"), nullable=False, unique=True)
    attitude_score = Column(Integer, nullable=False)
    understanding_score = Column(Integer, nullable=False)
    homework_score = Column(Integer, nullable=False)
    qa_score = Column(Integer, nullable=False)
    ai_comment_improvement = Column(Text)
    ai_comment_attitude = Column(Text)
    ai_comment_overall = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # Feedback -> Class (One-to-One)
    class_record = relationship("Class", back_populates="feedback")
