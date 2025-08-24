from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date

class TeacherCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class Teacher(BaseModel):
    """
    API 응답으로 사용할 선생님 정보 스키마 (비밀번호 제외)
    """
    teacher_id: int
    email: EmailStr
    name: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    """
    로그인 성공 시 반환될 JWT 액세스 토큰 스키마
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    JWT 토큰을 디코딩했을 때 얻게 될 데이터(payload) 스키마
    """
    email: Optional[EmailStr] = None
    
class FeedbackBase(BaseModel):
    attitude_score: int
    understanding_score: int
    homework_score: int
    qa_score: int

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackUpdate(BaseModel):
    ai_comment_improvement: Optional[str] = None
    ai_comment_attitude: Optional[str] = None
    ai_comment_overall: Optional[str] = None
        
class Feedback(FeedbackBase):
    feedback_id: int
    class_id: int
    ai_comment_improvement: Optional[str] = None
    ai_comment_attitude: Optional[str] = None
    ai_comment_overall: Optional[str] = None

    class Config:
        from_attributes = True


class ClassBase(BaseModel):
    subject: str
    class_date: date
    progress_text: Optional[str] = None
    class_memo: Optional[str] = None

class ClassCreate(ClassBase):
    pass

class Class(ClassBase):
    class_id: int
    student_id: int
    feedback: Optional[Feedback] = None

    class Config:
        from_attributes = True

class StudentBase(BaseModel):
    name: str
    grade: int

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    pass

class Student(StudentBase):
    student_id: int
    classes: List[Class] = []

    class Config:
        from_attributes = True

class FeedbackCreateRequest(BaseModel):
    """
    피드백 생성 API (POST /students/{student_id}/feedbacks)의
    Request Body를 위한 스키마
    """
    class_info: ClassCreate
    feedback_info: FeedbackCreate

Class.update_forward_refs()
