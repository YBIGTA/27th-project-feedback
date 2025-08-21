#!/usr/bin/env python3
"""
RDS 데이터베이스 연결 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_rds_connection():
    """RDS 데이터베이스 연결을 테스트합니다."""
    try:
        from backend.database import test_db_connection
        return test_db_connection()
    except ImportError as e:
        print(f"❌ 모듈 import 실패: {e}")
        print("프로젝트 루트 디렉토리에서 실행하세요.")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def check_environment_variables():
    """필요한 환경 변수가 설정되어 있는지 확인합니다."""
    required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing_vars = []
    
    print("🔍 환경 변수 확인 중...")
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 비밀번호는 마스킹하여 표시
            if var == 'DB_PASSWORD':
                masked_value = '*' * min(len(value), 8)
                print(f"  ✅ {var}: {masked_value}")
            else:
                print(f"  ✅ {var}: {value}")
        else:
            print(f"  ❌ {var}: 설정되지 않음")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        print("   .env 파일을 확인하거나 환경 변수를 설정하세요.")
        return False
    
    print("\n✅ 모든 필수 환경 변수가 설정되었습니다.")
    return True

def main():
    """메인 함수"""
    print("🚀 RDS 데이터베이스 연결 테스트 시작\n")
    
    # 환경 변수 로드
    load_dotenv()
    
    # 환경 변수 확인
    if not check_environment_variables():
        print("\n❌ 환경 변수 설정이 완료되지 않았습니다.")
        print("RDS_SETUP.md 파일을 참고하여 설정을 완료하세요.")
        return
    
    print("\n🔌 데이터베이스 연결 테스트 중...")
    
    # 연결 테스트
    if test_rds_connection():
        print("\n🎉 RDS 데이터베이스 연결이 성공적으로 설정되었습니다!")
        print("이제 애플리케이션을 실행할 수 있습니다.")
    else:
        print("\n💥 RDS 데이터베이스 연결에 실패했습니다.")
        print("다음을 확인하세요:")
        print("  1. RDS 인스턴스가 실행 중인지 확인")
        print("  2. 보안 그룹에서 포트 3306이 열려있는지 확인")
        print("  3. 데이터베이스 이름이 올바른지 확인")
        print("  4. 사용자명과 비밀번호가 올바른지 확인")

if __name__ == "__main__":
    main()
