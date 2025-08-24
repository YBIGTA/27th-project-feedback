from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from .. import crud, schemas, security
from ..database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# APIRouter 인스턴스 생성
router = APIRouter(
    tags=["Authentication"]
)

def get_current_teacher(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> schemas.Teacher:
    """
    JWT 토큰을 검증하고 현재 로그인된 선생님 정보를 반환하는 의존성 함수
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="유효한 자격 증명을 찾을 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 1. 토큰 디코딩
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        # 2. 토큰 데이터 유효성 검사
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # 3. DB에서 사용자 정보 조회
    teacher = crud.get_teacher_by_email(db, email=token_data.email)
    if teacher is None:
        raise credentials_exception
        
    return teacher

@router.post("/teachers/", response_model=schemas.Teacher, status_code=status.HTTP_201_CREATED)
def create_teacher_signup(teacher: schemas.TeacherCreate, db: Session = Depends(get_db)):
    """
    회원가입 엔드포인트
    """
    # 이메일 중복 체크
    db_teacher = crud.get_teacher_by_email(db, email=teacher.email)
    if db_teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다."
        )
    
    # 신규 선생님 생성
    return crud.create_teacher(db=db, teacher=teacher)


@router.post("/auth/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    로그인 및 JWT 토큰 발급 엔드포인트
    """
    # 1. 사용자 확인
    teacher = crud.get_teacher_by_email(db, email=form_data.username)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 2. 비밀번호 검증
    if not security.verify_password(form_data.password, teacher.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. JWT 생성
    access_token = security.create_access_token(
        data={"sub": teacher.email}
    )
    
    # 4. 토큰 반환
    return {"access_token": access_token, "token_type": "bearer"}