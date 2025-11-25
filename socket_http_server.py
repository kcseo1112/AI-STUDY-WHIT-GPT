import json
import os
import shutil
import socket
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import whisper

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
BASE_DIR = Path(__file__).parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
TRANSCRIPT_DIR = STORAGE_DIR / "transcripts"
SUMMARY_DIR = STORAGE_DIR / "summaries"
QUIZ_DIR = STORAGE_DIR / "quizzes"
METADATA_PATH = STORAGE_DIR / "metadata.json"
INDEX_FILE = BASE_DIR / "final_index.html"
WHISPER_MODEL_NAME = os.environ.get("WHISPER_MODEL", "base")

metadata_lock = threading.Lock()
whisper_model = None


def ensure_directories() -> None:
    """Ensure storage directories exist."""
    for directory in (UPLOAD_DIR, TRANSCRIPT_DIR, SUMMARY_DIR, QUIZ_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    if not METADATA_PATH.exists():
        save_metadata({"uploads": [], "transcripts": [], "summaries": [], "quizzes": []})


def load_metadata() -> Dict:
    with METADATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_metadata(data: Dict) -> None:
    with metadata_lock:
        with METADATA_PATH.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def http_response(status_code: int, headers: Dict[str, str], body: bytes) -> bytes:
    reason_phrases = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        500: "Internal Server Error",
    }
    reason = reason_phrases.get(status_code, "OK")
    header_lines = [f"HTTP/1.1 {status_code} {reason}"]
    headers = {**headers, "Content-Length": str(len(body)), "Connection": "close", "Access-Control-Allow-Origin": "*"}
    for key, value in headers.items():
        header_lines.append(f"{key}: {value}")
    header_lines.append("")
    header_lines.append("")
    return "\r\n".join(header_lines).encode("utf-8") + body


def parse_request(client_conn: socket.socket) -> Tuple[str, str, Dict[str, str], bytes]:
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = client_conn.recv(4096)
        if not chunk:
            break
        data += chunk
    if b"\r\n\r\n" not in data:
        raise ValueError("Malformed HTTP request")

    header_part, body = data.split(b"\r\n\r\n", 1)
    header_lines = header_part.decode("iso-8859-1").split("\r\n")
    request_line = header_lines[0]
    method, path, _ = request_line.split(" ", 2)
    headers = {}
    for line in header_lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    content_length = int(headers.get("content-length", "0"))
    while len(body) < content_length:
        body += client_conn.recv(4096)

    return method.upper(), path, headers, body


def serve_static(path: str) -> bytes:
    if path == "/":
        target = INDEX_FILE
    else:
        target = (BASE_DIR / path.lstrip("/")).resolve()
        if not str(target).startswith(str(BASE_DIR)):
            return http_response(404, {"Content-Type": "text/plain; charset=utf-8"}, b"Not Found")

    if not target.exists() or not target.is_file():
        return http_response(404, {"Content-Type": "text/plain; charset=utf-8"}, b"Not Found")

    mime = "text/html" if target.suffix == ".html" else "application/octet-stream"
    with target.open("rb") as f:
        content = f.read()
    return http_response(200, {"Content-Type": f"{mime}; charset=utf-8"}, content)


def parse_multipart(body: bytes, boundary: str) -> Dict[str, bytes]:
    parts = {}
    boundary_bytes = ("--" + boundary).encode()
    for segment in body.split(boundary_bytes):
        if not segment or segment in (b"--\r\n", b"--"):
            continue
        if segment.startswith(b"\r\n"):
            segment = segment[2:]
        if segment.endswith(b"\r\n"):
            segment = segment[:-2]
        header_block, content = segment.split(b"\r\n\r\n", 1)
        headers = header_block.decode("iso-8859-1").split("\r\n")
        disposition = [h for h in headers if h.lower().startswith("content-disposition")]
        if not disposition:
            continue
        dispo = disposition[0]
        name = ""
        filename = None
        for item in dispo.split(";"):
            item = item.strip()
            if item.startswith("name="):
                name = item.split("=", 1)[1].strip('"')
            elif item.startswith("filename="):
                filename = item.split("=", 1)[1].strip('"')
        parts[name] = (filename, content)
    return parts


def handle_upload(headers: Dict[str, str], body: bytes) -> bytes:
    content_type = headers.get("content-type", "")
    if "multipart/form-data" not in content_type or "boundary=" not in content_type:
        return http_response(400, {"Content-Type": "application/json"}, b'{"error":"invalid content type"}')

    boundary = content_type.split("boundary=")[1]
    parts = parse_multipart(body, boundary)
    file_part = parts.get("file")
    if not file_part:
        return http_response(400, {"Content-Type": "application/json"}, b'{"error":"file field missing"}')

    filename, content = file_part
    if not filename:
        filename = f"upload_{int(time.time())}"
    safe_name = filename.replace("/", "_").replace("\\", "_")
    target_path = UPLOAD_DIR / safe_name
    with target_path.open("wb") as f:
        f.write(content)

    meta = load_metadata()
    record = {
        "filename": safe_name,
        "path": str(target_path.relative_to(STORAGE_DIR)),
        "size": len(content),
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
    }
    meta["uploads"].append(record)
    save_metadata(meta)

    response = json.dumps({"status": "ok", "file": record}, ensure_ascii=False).encode("utf-8")
    return http_response(201, {"Content-Type": "application/json; charset=utf-8"}, response)


def load_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = whisper.load_model(WHISPER_MODEL_NAME)
    return whisper_model


def handle_transcribe(body: bytes) -> bytes:
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return http_response(400, {"Content-Type": "application/json"}, b'{"error":"invalid json"}')

    file_path = payload.get("file_path")
    if not file_path:
        return http_response(400, {"Content-Type": "application/json"}, b'{"error":"file_path required"}')

    target_file = STORAGE_DIR / file_path
    if not target_file.exists():
        return http_response(404, {"Content-Type": "application/json"}, b'{"error":"file not found"}')

    if shutil.which("ffmpeg") is None:
        error_message = {
            "error": "ffmpeg가 설치되어 있지 않아 STT 변환을 실행할 수 없습니다. ffmpeg 설치 후 다시 시도하세요.",
            "hint": "https://ffmpeg.org/download.html",
        }
        return http_response(500, {"Content-Type": "application/json; charset=utf-8"}, json.dumps(error_message, ensure_ascii=False).encode("utf-8"))

    try:
        model = load_whisper_model()
        result = model.transcribe(str(target_file))
    except FileNotFoundError as exc:
        message = str(exc)
        if "ffmpeg" in message.lower():
            message = "ffmpeg 실행 파일을 찾을 수 없습니다. 시스템 PATH에 ffmpeg를 추가한 뒤 다시 시도하세요."
        error_payload = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        return http_response(500, {"Content-Type": "application/json; charset=utf-8"}, error_payload)
    except Exception as exc:  # noqa: BLE001
        error_payload = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
        return http_response(500, {"Content-Type": "application/json; charset=utf-8"}, error_payload)
    transcript_text = result.get("text", "")

    transcript_name = target_file.stem + "_transcript.txt"
    transcript_path = TRANSCRIPT_DIR / transcript_name
    transcript_path.write_text(transcript_text, encoding="utf-8")

    meta = load_metadata()
    record = {
        "source": str(target_file.relative_to(STORAGE_DIR)),
        "transcript": str(transcript_path.relative_to(STORAGE_DIR)),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    meta["transcripts"].append(record)
    save_metadata(meta)

    response = json.dumps({"status": "ok", "transcript_path": record["transcript"], "text": transcript_text}, ensure_ascii=False).encode("utf-8")
    return http_response(201, {"Content-Type": "application/json; charset=utf-8"}, response)


def tokenize(text: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for token in text.replace("\n", " ").split(" "):
        token = token.strip(" ,.!?;:\"()[]{}\t").lower()
        if not token:
            continue
        counts[token] = counts.get(token, 0) + 1
    return counts


def simple_summary(text: str, max_sentences: int = 3) -> str:
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    scores = []
    freq = tokenize(text)
    for sentence in sentences:
        score = sum(freq.get(word.lower(), 0) for word in sentence.split())
        scores.append((score, sentence))
    top = sorted(scores, key=lambda x: x[0], reverse=True)[:max_sentences]
    return "\n".join(s for _, s in top) if top else text[:500]


def handle_summarize(body: bytes) -> bytes:
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return http_response(400, {"Content-Type": "application/json"}, b'{"error":"invalid json"}')

    text = payload.get("text")
    transcript_path = payload.get("transcript_path")
    if not text and transcript_path:
        file_path = STORAGE_DIR / transcript_path
        if not file_path.exists():
            return http_response(404, {"Content-Type": "application/json"}, b'{"error":"transcript not found"}')
        text = file_path.read_text(encoding="utf-8")

    if not text:
        return http_response(400, {"Content-Type": "application/json"}, b'{"error":"text required"}')

    summary = simple_summary(text)
    summary_name = f"summary_{int(time.time())}.txt"
    summary_path = SUMMARY_DIR / summary_name
    summary_path.write_text(summary, encoding="utf-8")

    meta = load_metadata()
    record = {
        "summary": str(summary_path.relative_to(STORAGE_DIR)),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    meta["summaries"].append(record)
    save_metadata(meta)

    response = json.dumps({"status": "ok", "summary_path": record["summary"], "summary": summary}, ensure_ascii=False).encode("utf-8")
    return http_response(201, {"Content-Type": "application/json; charset=utf-8"}, response)


def generate_quiz(text: str) -> str:
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    quiz_lines = []
    for idx, sentence in enumerate(sentences[:3], start=1):
        tokens = [t for t in sentence.split() if len(t) > 4]
        blank = tokens[0] if tokens else "______"
        quiz_lines.append(f"Q{idx}. 다음 문장을 완성하세요: {sentence.replace(blank, '_____', 1)}")
        quiz_lines.append(f"A{idx}. 정답: {blank}")
        quiz_lines.append("")
    if not quiz_lines:
        quiz_lines.append("Q1. 입력된 요약에서 핵심 키워드를 작성하세요.")
        quiz_lines.append("A1. 사용자 해석에 따라 달라질 수 있습니다.")
    return "\n".join(quiz_lines)


def handle_quiz(body: bytes) -> bytes:
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return http_response(400, {"Content-Type": "application/json"}, b'{"error":"invalid json"}')

    text = payload.get("text") or ""
    summary_path = payload.get("summary_path")
    if summary_path:
        file_path = STORAGE_DIR / summary_path
        if not file_path.exists():
            return http_response(404, {"Content-Type": "application/json"}, b'{"error":"summary not found"}')
        text = text or file_path.read_text(encoding="utf-8")

    if not text:
        return http_response(400, {"Content-Type": "application/json"}, b'{"error":"text required"}')

    quiz = generate_quiz(text)
    quiz_name = f"quiz_{int(time.time())}.txt"
    quiz_path = QUIZ_DIR / quiz_name
    quiz_path.write_text(quiz, encoding="utf-8")

    meta = load_metadata()
    record = {
        "quiz": str(quiz_path.relative_to(STORAGE_DIR)),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    meta["quizzes"].append(record)
    save_metadata(meta)

    response = json.dumps({"status": "ok", "quiz_path": record["quiz"], "quiz": quiz}, ensure_ascii=False).encode("utf-8")
    return http_response(201, {"Content-Type": "application/json; charset=utf-8"}, response)


def handle_client(client_conn: socket.socket, address: Tuple[str, int]) -> None:
    try:
        method, path, headers, body = parse_request(client_conn)
    except Exception as exc:  # noqa: BLE001
        response = http_response(400, {"Content-Type": "text/plain; charset=utf-8"}, f"Bad Request: {exc}".encode("utf-8"))
        client_conn.sendall(response)
        client_conn.close()
        return

    try:
        if method == "GET":
            response = serve_static(path)
        elif method == "POST":
            if path == "/api/upload":
                response = handle_upload(headers, body)
            elif path == "/api/transcribe":
                response = handle_transcribe(body)
            elif path == "/api/summarize":
                response = handle_summarize(body)
            elif path == "/api/quiz":
                response = handle_quiz(body)
            else:
                response = http_response(404, {"Content-Type": "application/json"}, b'{"error":"not found"}')
        else:
            response = http_response(405, {"Content-Type": "application/json"}, b'{"error":"method not allowed"}')
    except Exception as exc:  # noqa: BLE001
        error_message = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
        response = http_response(500, {"Content-Type": "application/json; charset=utf-8"}, error_message)

    client_conn.sendall(response)
    client_conn.close()


def run_server() -> None:
    ensure_directories()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"[SERVER] Listening on {HOST}:{PORT}")
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()


if __name__ == "__main__":
    run_server()
