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

## 동작 방식

이 프로젝트는 프레임워크 없이 **소켓 + 스레드 기반으로 직접 HTTP를 파싱**하는 서버(`http_server.py`)와, 이를 호출하는 단일 HTML 클라이언트(`final_index.html`)로 구성됩니다. 브라우저는 HTTP 요청을 통해 서버와 통신하며, OpenAI API 키를 설정하면 STT(Whisper)·요약·퀴즈 생성이 외부 GPT 엔진을 통해 수행됩니다. 키가 없으면 간단한 로컬 휴리스틱이 대체합니다.

## VS Code에서 실행하는 법

1. VS Code에서 이 폴더를 열고 터미널을 하나 엽니다.
2. (선택) OpenAI를 쓰려면 위 환경변수를 터미널에 먼저 export 합니다.
3. 터미널에서 `python http_server.py` 실행 후, VS Code 우측 하단 안내 메시지가 뜨면 **포트 8080 포워딩/열기**를 허용합니다.
4. 브라우저(또는 VS Code 포트 포워딩 미리보기)에서 `http://localhost:8080/` 접속 후 UI에서 로그인 → 업로드 → 변환/요약/퀴즈 생성 플로우를 진행합니다.
5. 서버 로그는 터미널에 실시간으로 출력되며, 업로드/결과 파일은 `data/` 하위에 저장됩니다.

## 점검용 체크리스트

- 서버가 `Serving on 0.0.0.0:8080` 로그를 출력하는지 확인
- 업로드 시 `data/uploads/`에 파일이 생성되는지 확인
- OpenAI 키가 설정된 경우 STT/요약/퀴즈 생성 요청이 외부 API를 호출하는지 로그에서 확인
- 키가 없을 경우에도 요약/퀴즈가 간단한 규칙 기반으로 동작하는지 UI에서 확인
