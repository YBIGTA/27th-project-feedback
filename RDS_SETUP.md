# RDS 데이터베이스 설정 가이드

## 1. RDS 인스턴스 생성

### AWS RDS 콘솔에서 다음 설정으로 MySQL 인스턴스를 생성하세요:

- **엔진**: MySQL 8.0
- **템플릿**: 프로덕션 또는 개발/테스트
- **인스턴스 크기**: db.t3.micro (개발용) 또는 db.t3.small (프로덕션용)
- **스토리지**: 20GB (자동 확장 활성화)
- **멀티 AZ**: 프로덕션 환경에서는 활성화 권장
- **퍼블릭 액세스**: 개발용은 활성화, 프로덕션용은 비활성화 권장

- 


## 2. 보안 그룹 설정

### 인바운드 규칙 추가:
- **포트**: 3306
- **소스**: 애플리케이션 서버의 보안 그룹 또는 IP 주소
- **프로토콜**: TCP

## 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 추가하세요:

```bash
# RDS 데이터베이스 설정
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database_name

# RDS SSL 설정 (필요시)
SSL_CA=/path/to/rds-ca-2019-root.pem
SSL_VERIFY=false

# OpenAI API 키 (AI 피드백 기능용)
OPENAI_API_KEY=your_openai_api_key

# 기타 설정
DEBUG=false
ENVIRONMENT=production
```

## 4. 데이터베이스 생성

RDS 인스턴스에 연결하여 데이터베이스를 생성하세요:

```sql
CREATE DATABASE your_database_name CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 5. 테이블 생성

애플리케이션을 실행하면 SQLAlchemy가 자동으로 테이블을 생성합니다:

```bash
python -c "from backend.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## 6. 연결 테스트

```bash
python -c "from backend.database import test_db_connection; test_db_connection()"
```

## 7. SSL 인증서 다운로드 (필요시)

AWS RDS SSL 인증서를 다운로드하여 사용할 수 있습니다:

```bash
wget https://s3.amazonaws.com/rds-downloads/rds-ca-2019-root.pem
```

## 8. 모니터링 및 백업

- **백업 보존 기간**: 7일 (개발용) 또는 30일 (프로덕션용)
- **자동 백업**: 활성화
- **유지 관리 기간**: 애플리케이션 사용량이 적은 시간대 설정

## 9. 비용 최적화

- **예약 인스턴스**: 1년 또는 3년 약정으로 비용 절약
- **스토리지 자동 확장**: 필요에 따라 자동으로 스토리지 확장
- **비활성 시간**: 개발 환경에서는 사용하지 않을 때 인스턴스를 중지

## 10. 보안 체크리스트

- [ ] 강력한 비밀번호 사용
- [ ] 최소 권한 원칙 적용
- [ ] SSL/TLS 연결 사용
- [ ] 정기적인 보안 패치 적용
- [ ] 접근 로그 모니터링
- [ ] 백업 암호화 활성화
