# env_utils.py
# 환경 변수 유틸리티 모듈 (.env 파일에서 읽기)

import os

# .env 파일에서 환경 변수 로드
def load_env_file():
    """.env 파일에서 환경 변수 로드"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 주석이나 빈 줄 무시
                    if not line or line.startswith('#'):
                        continue
                    # KEY=VALUE 형식 파싱
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
        except Exception as e:
            print(f"환경 변수 파일 로드 오류: {e}")

# .env 파일 로드
load_env_file()

# 환경 변수 읽기 함수들 (.env 파일에서만 읽기)
def get_default_host():
    value = os.getenv('DEFAULT_HOST')
    if value is None:
        raise ValueError("DEFAULT_HOST가 .env 파일에 설정되어 있지 않습니다.")
    return value

def get_default_port():
    value = os.getenv('DEFAULT_PORT')
    if value is None:
        raise ValueError("DEFAULT_PORT가 .env 파일에 설정되어 있지 않습니다.")
    return int(value)

def get_bufsize():
    value = os.getenv('BUFSIZE')
    if value is None:
        raise ValueError("BUFSIZE가 .env 파일에 설정되어 있지 않습니다.")
    return int(value)

def get_receive_dir():
    value = os.getenv('RECEIVE_DIR')
    if value is None:
        raise ValueError("RECEIVE_DIR이 .env 파일에 설정되어 있지 않습니다.")
    return value

def get_data_dir():
    value = os.getenv('DATA_DIR')
    if value is None:
        raise ValueError("DATA_DIR이 .env 파일에 설정되어 있지 않습니다.")
    return value

def get_supabase_url():
    value = os.getenv('SUPABASE_URL')
    if value is None:
        raise ValueError("SUPABASE_URL이 .env 파일에 설정되어 있지 않습니다.")
    return value

def get_supabase_anon_key():
    value = os.getenv('SUPABASE_ANON_KEY')
    if value is None:
        raise ValueError("SUPABASE_ANON_KEY가 .env 파일에 설정되어 있지 않습니다.")
    return value

def get_openai_api_key():
    return os.getenv('OPENAI_API_KEY', '')  # OpenAI는 선택사항이므로 빈 문자열 허용

def get_openai_model():
    value = os.getenv('OPENAI_MODEL')
    if value is None:
        raise ValueError("OPENAI_MODEL이 .env 파일에 설정되어 있지 않습니다.")
    return value

def get_whisper_model():
    """Whisper 모델 설정 (OpenAI Whisper API는 'whisper-1'만 사용, 호환성을 위해 유지)"""
    # OpenAI Whisper API는 'whisper-1' 모델만 사용하므로 기본값 반환
    return os.getenv('WHISPER_MODEL', 'whisper-1')

def get_whisper_language():
    """Whisper 언어 설정 (선택사항, 없으면 자동 감지)"""
    # OpenAI Whisper API는 language가 없으면 자동 감지하므로 선택사항
    return os.getenv('WHISPER_LANGUAGE', None)

# 호환성을 위한 상수 (기존 코드와의 호환)
DEFAULT_HOST = get_default_host()
DEFAULT_PORT = get_default_port()
BUFSIZE = get_bufsize()
RECEIVE_DIR = get_receive_dir()
DATA_DIR = get_data_dir()
SUPABASE_URL = get_supabase_url()
SUPABASE_ANON_KEY = get_supabase_anon_key()
OPENAI_API_KEY = get_openai_api_key()
OPENAI_MODEL = get_openai_model()
WHISPER_MODEL = get_whisper_model()
WHISPER_LANGUAGE = get_whisper_language()

