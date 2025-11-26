# AI 기반 학습 지원 시스템

이 저장소는 프레임워크 없이 `socket` + `threading` 기반으로 동작하는 학습 지원용 HTTP 서버와 예시 HTML UI를 포함합니다. 음성(STT) 변환, 요약, 문제 생성 흐름을 단일 서버에서 처리하도록 구성했습니다.

## 기능 개요
- **파일 업로드**: multipart/form-data를 직접 파싱해 업로드 파일을 `storage/uploads`에 저장합니다.
- **STT 변환**: `openai-whisper` 로컬 모델을 사용해 녹음 파일을 텍스트로 변환합니다.
- **요약 생성**: 간단한 토큰 빈도 기반 요약기로 핵심 문장을 추출합니다.
- **퀴즈 생성**: 요약 결과를 바탕으로 예시 객관식/주관식 문제를 생성하고 저장합니다.
- **정적 자원 제공**: 기본 UI(`final_index.html`)를 HTTP GET으로 서빙합니다.

## 빠른 시작
1. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
   > `openai-whisper`는 `ffmpeg`와 `torch`를 필요로 합니다. 로컬 환경에 맞춰 사전 설치해 주세요.

2. 서버 실행
   ```bash
   python socket_http_server.py [--host 0.0.0.0] [--port 8080]
   ```
   기본 포트는 `8080`이며 환경 변수 `PORT` 또는 `--port` 옵션으로 변경할 수 있습니다. 다른 기기에서 접속하려면 `--host 0.0.0.0`(또는 해당 머신의 IP)으로 실행 후 출력되는 "다른 기기 접속 URL"을 사용하세요.

3. 브라우저에서 접속
   - `http://localhost:8080/` 접속 후 제공된 HTML을 사용해 파일 업로드, 변환, 요약, 퀴즈 생성 기능을 테스트합니다.

## 주요 엔드포인트
- `GET /` : `final_index.html` 반환
- `POST /api/upload` : `multipart/form-data`의 `file` 필드 업로드
- `POST /api/transcribe` : `{ "file_path": "uploads/파일명" }` JSON으로 STT 실행
- `POST /api/summarize` : `{ "text": "..." }` 또는 `{ "transcript_path": "..." }`
- `POST /api/quiz` : `{ "text": "..." }` 혹은 `{ "summary_path": "..." }`

## 데이터 저장 구조
- `storage/metadata.json` : 업로드/요약/퀴즈 메타데이터 저장
- `storage/uploads` : 업로드 원본 파일
- `storage/transcripts` : STT 결과 텍스트 파일
- `storage/summaries` : 요약 결과 텍스트 파일
- `storage/quizzes` : 생성된 문제 텍스트 파일

## 개발 메모
- 모든 HTTP 요청 파싱, 라우팅, 응답 포맷을 직접 구현했습니다. 프레임워크를 사용하지 않습니다.
- Whisper 모델은 처음 로드 시 시간이 걸릴 수 있습니다. 환경 변수 `WHISPER_MODEL`(기본값 `base`)로 모델 크기를 조정할 수 있습니다.
