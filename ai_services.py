# ai_services.py
# AI 서비스 통합 모듈 (OpenAI Whisper API)

import os

# OpenAI API 클라이언트 (env_utils.py에서 환경 변수 로드됨)
try:
    from env_utils import OPENAI_API_KEY
    if OPENAI_API_KEY:
        from openai import OpenAI
        # 타임아웃 설정: STT 처리는 큰 파일의 경우 시간이 걸릴 수 있음
        # connect timeout: 10초, read timeout: 300초 (5분)
        import httpx
        openai_client = OpenAI(
            api_key=OPENAI_API_KEY,
            timeout=httpx.Timeout(10.0, read=300.0)  # 연결 10초, 읽기 5분
        )
        OPENAI_AVAILABLE = True
        OPENAI_ERROR = None
    else:
        openai_client = None
        OPENAI_AVAILABLE = False
        OPENAI_ERROR = "OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다."
except ImportError:
    openai_client = None
    OPENAI_AVAILABLE = False
    OPENAI_ERROR = "openai 모듈을 찾을 수 없습니다."
except Exception as e:
    openai_client = None
    OPENAI_AVAILABLE = False
    OPENAI_ERROR = str(e)

# STT 기능은 OpenAI Whisper API를 사용하므로 OPENAI_AVAILABLE과 동일
STT_AVAILABLE = OPENAI_AVAILABLE
STT_ERROR = OPENAI_ERROR


def transcribe_audio(file_path, language=None, model_name=None):
    """오디오 파일을 텍스트로 변환 (OpenAI Whisper API)"""
    if not OPENAI_AVAILABLE or not openai_client:
        raise RuntimeError(f"OpenAI API를 사용할 수 없습니다: {OPENAI_ERROR}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
    
    # 파일 크기 확인 (OpenAI Whisper API는 25MB 제한)
    file_size = os.path.getsize(file_path)
    max_size = 25 * 1024 * 1024  # 25MB
    if file_size > max_size:
        raise ValueError(f"파일 크기가 너무 큽니다 ({file_size / 1024 / 1024:.2f}MB). 최대 25MB까지 지원됩니다.")
    
    # OpenAI Whisper API 사용
    # language 파라미터는 ISO 639-1 형식 (예: 'ko', 'en')
    # model은 'whisper-1'만 사용 가능 (기본값)
    from env_utils import WHISPER_LANGUAGE
    
    try:
        # 파일 열기
        with open(file_path, 'rb') as audio_file:
            # 파일명에서 확장자 추출하여 파일명 지정
            filename = os.path.basename(file_path)
            
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=(filename, audio_file, None),  # (filename, file_object, content_type) 튜플 형식
                language=language or WHISPER_LANGUAGE or None,  # None이면 자동 감지
                response_format="text"
            )
        
        return transcript
    except Exception as e:
        error_msg = f"STT 변환 중 오류 발생: {str(e)}"
        # OpenAI API 오류 메시지 개선
        if "timeout" in str(e).lower():
            error_msg += "\n\n타임아웃이 발생했습니다. 파일이 너무 크거나 네트워크 연결이 불안정할 수 있습니다."
        elif "invalid" in str(e).lower() or "format" in str(e).lower():
            error_msg += "\n\n지원되지 않는 파일 형식일 수 있습니다. 지원 형식: mp3, mp4, mpeg, mpga, m4a, wav, webm"
        elif "rate_limit" in str(e).lower():
            error_msg += "\n\nAPI 사용량 제한에 도달했습니다. 잠시 후 다시 시도해주세요."
        raise RuntimeError(error_msg) from e


def generate_keywords(text):
    """텍스트에서 키워드 추출 (OpenAI)"""
    if not OPENAI_AVAILABLE or not openai_client:
        raise RuntimeError(f"OpenAI API를 사용할 수 없습니다: {OPENAI_ERROR}")
    
    prompt = f"""다음 텍스트에서 주요 키워드를 5-10개 추출해주세요. 
키워드는 쉼표로 구분하여 한국어로 나열해주세요.

텍스트:
{text}

키워드:"""
    
    from env_utils import OPENAI_MODEL
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content.strip()


def generate_summary(text):
    """텍스트 요약 생성 (OpenAI)"""
    if not OPENAI_AVAILABLE or not openai_client:
        raise RuntimeError(f"OpenAI API를 사용할 수 없습니다: {OPENAI_ERROR}")
    
    prompt = f"""다음 텍스트를 핵심 내용만 간단히 요약해주세요 (3-5문장).

텍스트:
{text}

요약:"""
    
    from env_utils import OPENAI_MODEL
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content.strip()


def generate_quiz(text, count=5):
    """퀴즈 생성 (OpenAI) - 여러 문제"""
    if not OPENAI_AVAILABLE or not openai_client:
        raise RuntimeError(f"OpenAI API를 사용할 수 없습니다: {OPENAI_ERROR}")
    
    import json
    
    prompt = f"""다음 텍스트를 기반으로 {count}개의 퀴즈 문제를 생성해주세요. 
각 문제는 주관식 형식이어야 하며, 정답과 해설을 포함해주세요.

텍스트:
{text}

JSON 형식으로 응답해주세요:
{{
  "questions": [
    {{
      "question": "문제 내용",
      "answer": "정답",
      "explanation": "해설"
    }}
  ]
}}"""
    
    from env_utils import OPENAI_MODEL
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    
    result_text = response.choices[0].message.content
    # JSON 추출 (마크다운 코드 블록 제거)
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()
    
    return json.loads(result_text)


def generate_single_quiz(text, existing_questions=None):
    """퀴즈 한 문제 생성 (OpenAI) - 기존 문제와 중복되지 않도록"""
    if not OPENAI_AVAILABLE or not openai_client:
        raise RuntimeError(f"OpenAI API를 사용할 수 없습니다: {OPENAI_ERROR}")
    
    import json
    
    existing_text = ""
    if existing_questions:
        existing_text = "\n\n이미 생성된 문제들 (중복되지 않도록):\n"
        for idx, q in enumerate(existing_questions, 1):
            existing_text += f"{idx}. {q.get('question', '')}\n"
    
    prompt = f"""다음 텍스트를 기반으로 퀴즈 문제 1개를 생성해주세요. 
주관식 형식이어야 하며, 정답과 해설을 포함해주세요.
{existing_text}

텍스트:
{text}

JSON 형식으로 응답해주세요:
{{
  "question": "문제 내용",
  "answer": "정답",
  "explanation": "해설"
}}"""
    
    from env_utils import OPENAI_MODEL
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    
    result_text = response.choices[0].message.content
    # JSON 추출 (마크다운 코드 블록 제거)
    if "```json" in result_text:
        result_text = result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        result_text = result_text.split("```")[1].split("```")[0].strip()
    
    return json.loads(result_text)


def analyze_text(text, analysis_type="summary"):
    """텍스트 분석 (키워드 또는 요약)"""
    if analysis_type == "keyword":
        return generate_keywords(text)
    else:
        return generate_summary(text)


