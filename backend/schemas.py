from pydantic import BaseModel
from typing import List, Optional
from datetime import date

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
        orm_mode = True


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
        orm_mode = True

class StudentBase(BaseModel):
    name: str
    grade: int

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase): # <<<< ⭐️ 추가된 부분
    pass

class Student(StudentBase):
    student_id: int
    classes: List[Class] = []

    class Config:
        orm_mode = True

class FeedbackCreateRequest(BaseModel):
    """
    피드백 생성 API (POST /students/{student_id}/feedbacks)의
    Request Body를 위한 스키마
    """
    class_info: ClassCreate
    feedback_info: FeedbackCreate

Class.update_forward_refs()
