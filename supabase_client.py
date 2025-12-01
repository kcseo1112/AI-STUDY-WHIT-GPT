# supabase_client.py
# Supabase 클라이언트 모듈

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from supabase import create_client, Client
    SUPABASE_MODULE_AVAILABLE = True
except ImportError:
    SUPABASE_MODULE_AVAILABLE = False
    print("경고: supabase 모듈을 찾을 수 없습니다. pip install supabase 실행하세요.")
    Client = None

# env_utils.py에서 환경 변수 로드
from env_utils import SUPABASE_URL, SUPABASE_ANON_KEY

# Supabase 클라이언트 초기화
supabase: Client | None = None

if SUPABASE_MODULE_AVAILABLE and SUPABASE_URL and SUPABASE_ANON_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print("Supabase 클라이언트 초기화 완료")
    except Exception as e:
        print(f"Supabase 클라이언트 초기화 실패: {e}")
        supabase = None
else:
    if not SUPABASE_MODULE_AVAILABLE:
        print("경고: supabase 모듈이 설치되지 않았습니다.")
    elif not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("경고: Supabase 설정이 .env 파일에 없습니다.")
    supabase = None

SUPABASE_AVAILABLE = supabase is not None

