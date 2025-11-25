# AI-STUDY-WHIT-GPT

## Quick start (socket 기반 HTTP 서버)

1. 가상환경이 필요하지 않은 순수 Python 표준 라이브러리만 사용합니다.
2. OpenAI 연동이 필요하다면 환경변수를 설정합니다.

```bash
export OPENAI_API_KEY="sk-..."               # 필수
export OPENAI_API_BASE="https://api.openai.com/v1"  # 선택, 프록시/지역화 필요 시
export OPENAI_CHAT_MODEL="gpt-4o-mini"             # 선택, 다른 채팅 모델 사용 시
export OPENAI_TRANSCRIBE_MODEL="whisper-1"         # 선택, STT 모델 교체 시
```

3. 다음 명령으로 서버를 실행합니다.

```bash
python http_server.py
```

서버는 `0.0.0.0:8080`에서 동작하며, 브라우저에서 `http://localhost:8080/`을 열면 `final_index.html` UI가 제공됩니다.

### 주요 엔드포인트

* `POST /api/login` – 간단한 로그인/회원가입(저장 파일: `data/store.json`)
* `POST /api/upload` – `multipart/form-data` 파일 업로드 + **OpenAI Whisper(환경변수 설정 시)** STT 변환 + 요약/퀴즈 생성
* `POST /api/analyze` – 텍스트 요약·키워드·퀴즈 생성(**OpenAI Chat Completion 우선 사용, 키 미설정 시 간단 규칙 기반**)
* `GET /api/files` – 사용자별 업로드 목록 조회
* `POST/PUT/DELETE /api/folders` – 폴더 CRUD (email 쿼리 파라미터 사용)

### 데이터 저장 위치

* 업로드 파일: `data/uploads/`
* 메타데이터: `data/store.json`