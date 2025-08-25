import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

load_dotenv()

# RDS 환경 변수에서 데이터베이스 연결 정보 로드
DB_HOST = os.getenv("DB_HOST")  # RDS 엔드포인트
DB_PORT = os.getenv("DB_PORT", "3306")  # RDS 포트 (기본값: 3306)
DB_USER = os.getenv("DB_USER")  # RDS 사용자명
DB_PASSWORD = os.getenv("DB_PASSWORD")  # RDS 비밀번호
DB_NAME = os.getenv("DB_NAME")  # 데이터베이스명

# RDS SSL 설정
SSL_CA = os.getenv("SSL_CA", "")  # RDS SSL 인증서 경로 (필요시)
SSL_VERIFY = os.getenv("SSL_VERIFY", "false").lower() == "true"

# RDS 연결 URL 생성
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# RDS에 최적화된 SQLAlchemy 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "charset": "utf8mb4",
        "ssl": {
            "ssl_ca": SSL_CA if SSL_CA else None,
            "ssl_verify_cert": SSL_VERIFY,
        } if SSL_CA or SSL_VERIFY else {},
    },
    # RDS 연결 풀 설정
    poolclass=QueuePool,
    pool_size=10,  # 기본 연결 풀 크기
    max_overflow=20,  # 최대 추가 연결 수
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=3600,  # 1시간마다 연결 재생성
    echo=False,  # SQL 쿼리 로깅 (개발시 True로 설정)
)

# SessionLocal 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

# 데이터베이스 세션 생성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 데이터베이스 연결 테스트 함수
def test_db_connection():
    """RDS 데이터베이스 연결을 테스트합니다."""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            print("✅ RDS 데이터베이스 연결 성공!")
            return True
    except Exception as e:
        print(f"❌ RDS 데이터베이스 연결 실패: {e}")
        return False
