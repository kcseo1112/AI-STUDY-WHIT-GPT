# 핵심 통신/처리 코드 길잡이

클라이언트와 서버 간 파일·명령 통신 흐름을 이해하기 위한 필독 소스 파일과 주요 역할을 정리했습니다.

## 클라이언트 측
- `Client/client_core.py`: 요청당 새 TCP 소켓을 열어 명령(JSON)과 파일을 전송하는 핵심 로직.
  - `send_command`: JSON 본문 길이를 4바이트 헤더로 붙여 전송하고, 동일 포맷으로 응답을 수신합니다. STT처럼 시간이 걸리는 작업을 고려해 5분 타임아웃을 적용합니다.
  - `send_file`: 파일명을 NULL로 종료해 보낸 뒤 서버의 `READY` 신호를 기다리고, 파일 크기와 바이트 스트림을 전송합니다. 완료 후 `SUCCESS`/`ERROR`를 확인합니다.

## 서버 측
- `Server/server_core.py`: TCP 서버 엔트리포인트. 클라이언트 연결을 스레드로 분기하고, 수신 첫 4바이트를 스니핑해 명령/파일을 구분합니다.
  - `handle_command`: 길이 프레이밍된 JSON을 파싱해 라우팅하며, 응답도 동일한 4바이트 길이 헤더+본문으로 반환합니다.
  - `receive_file`: 파일명·크기를 NULL 종료 문자열로 받아 `RECEIVE_DIR`에 저장하고 `SUCCESS` 신호를 회신합니다.
  - `process_command`: 로그인/폴더 관리/파일 로드·목록/텍스트 분석·퀴즈 생성 등 비즈니스 명령을 `ServerCommandHandlers`로 위임합니다.
- `Server/server_handlers.py`: 명령별 실제 처리 구현.
  - `handle_convert_audio`, `handle_save_text`, `handle_analyze_text`, `handle_generate_quiz` 등이 OpenAI API 래퍼(`ai_services.py`)와 데이터 계층(`server_data_supabase.py` 또는 `server_data.py`)을 호출해 변환·저장·퀴즈 생성까지 처리합니다.

## 빠르게 시작하려면
1. 위 클라이언트/서버 코어 두 파일의 송수신 프로토콜(길이 헤더·NULL 종료 문자열·READY/SUCCESS 신호)을 먼저 확인합니다.
2. 그다음 `Server/server_handlers.py`에서 원하는 명령 흐름을 따라가며 데이터 저장·AI 호출 시나리오를 익히면 전체 작동 방식을 빠르게 파악할 수 있습니다.
