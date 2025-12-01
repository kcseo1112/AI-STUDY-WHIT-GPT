# AI 학습 지원 시스템

오디오 파일을 텍스트로 변환하고, AI를 활용하여 키워드 추출, 요약, 퀴즈 생성을 지원하는 시스템입니다.

## 프로젝트 구조

```
prototype_v3/
├── Client/              # 클라이언트 코드
│   ├── client_core.py   # TCP 통신 모듈
│   ├── client_gui.py    # GUI 메인
│   ├── client_handlers.py  # 이벤트 핸들러
│   └── client_ui.py     # UI 구성
├── Server/              # 서버 코드
│   ├── server_core.py   # 서버 핵심 기능
│   ├── server_data_supabase.py  # Supabase 데이터 관리
│   ├── server_data.py   # JSON 폴백 데이터 관리
│   ├── server_gui.py    # 서버 GUI
│   └── server_handlers.py  # 서버 명령 처리
├── ai_services.py       # OpenAI API 서비스
├── env_utils.py         # 환경 변수 관리
├── supabase_client.py   # Supabase 클라이언트
├── run_client.py        # 클라이언트 실행
├── run_server.py        # 서버 실행 (GUI)
├── run_server_console.py # 서버 실행 (콘솔)
├── requirements.txt     # 전체 패키지 의존성
├── requirements-client.txt  # 클라이언트 패키지 의존성
├── requirements-server.txt  # 서버 패키지 의존성
└── supabase_setup_simple.sql  # 데이터베이스 스키마

```

## 설치 및 실행

### 1. 환경 설정

`env.txt` 파일을 `.env`로 복사한 후 실제 값으로 채워주세요:

```bash
# Windows
copy env.txt .env

# Linux/Mac
cp env.txt .env
```

그 다음 `.env` 파일을 열어서 다음 정보를 실제 값으로 변경하세요:
- `OPENAI_API_KEY`: OpenAI API 키 (https://platform.openai.com/api-keys)
- `SUPABASE_URL`: Supabase 프로젝트 URL
- `SUPABASE_ANON_KEY`: Supabase 익명 키
- `DEFAULT_HOST`: 서버 호스트 주소 (예: 127.0.0.1 또는 실제 IP)
- 기타 필요한 설정값들

**⚠️ 중요**: `.env` 파일은 절대 GitHub에 올리지 마세요! 민감한 정보가 포함되어 있습니다.

### 2. 패키지 설치

```bash
# 전체 설치
pip install -r requirements.txt

# 또는 클라이언트만 설치
pip install -r requirements-client.txt

# 또는 서버만 설치
pip install -r requirements-server.txt
```

### 3. 데이터베이스 설정

Supabase 대시보드의 SQL Editor에서 `supabase_setup_simple.sql` 파일을 실행하세요.

### 4. 실행

**서버 실행:**
```bash
# GUI 모드
python run_server.py

# 콘솔 모드
python run_server_console.py
```

**클라이언트 실행:**
```bash
python run_client.py
```

## 주요 기능

1. **오디오 → 텍스트 변환**: OpenAI Whisper API를 사용하여 오디오 파일을 텍스트로 변환
2. **키워드 추출**: 변환된 텍스트에서 주요 키워드를 자동 추출
3. **요약 생성**: 텍스트의 핵심 내용을 요약
4. **퀴즈 생성**: 텍스트 기반으로 학습용 퀴즈 자동 생성
5. **데이터 저장**: File과 Quiz 테이블에 데이터 저장 (PostgreSQL/Supabase)

## 기술 스택

- **클라이언트**: Python, Tkinter
- **서버**: Python, TCP/IP 소켓 통신
- **데이터베이스**: PostgreSQL (Supabase)
- **AI 서비스**: OpenAI API (Whisper STT, GPT)

## 주의사항

- STT 변환은 클라이언트에서 OpenAI Whisper API를 직접 사용합니다.
- OpenAI API 키가 필요하며, 사용량에 따라 비용이 발생할 수 있습니다.
- 파일 크기는 최대 25MB까지 지원됩니다.

