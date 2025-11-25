import json
import mimetypes
import os
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

HOST = "0.0.0.0"
PORT = 8080
DATA_DIR = "data"
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
STORE_PATH = os.path.join(DATA_DIR, "store.json")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")

STATUS_TEXT = {
    200: "OK",
    201: "Created",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error",
}


def ensure_directories() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_store() -> Dict:
    if os.path.exists(STORE_PATH):
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": [],
        "folders": [],
        "files": [],
        "quizzes": [],
        "counters": {},
    }


def save_store(store: Dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def next_id(store: Dict, key: str) -> int:
    counters = store.setdefault("counters", {})
    counters[key] = counters.get(key, 0) + 1
    return counters[key]


def split_headers(raw_headers: bytes) -> Tuple[str, Dict[str, str]]:
    lines = raw_headers.decode("latin-1").split("\r\n")
    request_line = lines[0]
    headers = {}
    for line in lines[1:]:
        if not line:
            continue
        if ":" in line:
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()
    return request_line, headers


def parse_request(conn: socket.socket) -> Tuple[str, str, str, Dict[str, str], bytes]:
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk
    if not data:
        return "", "", "", {}, b""

    header_part, _, remainder = data.partition(b"\r\n\r\n")
    request_line, headers = split_headers(header_part)
    try:
        method, path, version = request_line.split(" ")
    except ValueError:
        return "", "", "", {}, b""

    content_length = int(headers.get("content-length", "0"))
    body = remainder
    while len(body) < content_length:
        chunk = conn.recv(min(4096, content_length - len(body)))
        if not chunk:
            break
        body += chunk
    return method, path, version, headers, body


def send_response(conn: socket.socket, status: int, headers: Dict[str, str], body: bytes = b"") -> None:
    status_text = STATUS_TEXT.get(status, "OK")
    response_headers = {
        "Content-Length": str(len(body)),
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        **headers,
    }
    header_lines = "\r\n".join(f"{k}: {v}" for k, v in response_headers.items())
    response = f"HTTP/1.1 {status} {status_text}\r\n{header_lines}\r\n\r\n".encode("latin-1") + body
    conn.sendall(response)


def call_openai_chat(messages: List[Dict[str, str]], max_tokens: int = 400) -> Optional[str]:
    if not OPENAI_API_KEY:
        return None
    payload = {
        "model": OPENAI_CHAT_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{OPENAI_API_BASE}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as resp:
            result = json.load(resp)
            return result.get("choices", [{}])[0].get("message", {}).get("content")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def summarize_text(text: str, limit: int = 2) -> str:
    if OPENAI_API_KEY:
        prompt = [
            {
                "role": "system",
                "content": "주어진 학습 자료를 3문장 이내로 한국어 요약하세요.",
            },
            {"role": "user", "content": text[:8000]},
        ]
        summary = call_openai_chat(prompt, max_tokens=300)
        if summary:
            return summary.strip()
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    summary = " ".join(sentences[:limit]).strip()
    return summary or text[:200]


def extract_keywords(text: str, top_k: int = 5) -> List[str]:
    if OPENAI_API_KEY:
        prompt = [
            {"role": "system", "content": "주요 키워드를 쉼표로 구분하여 최대 5개만 출력하세요."},
            {"role": "user", "content": text[:8000]},
        ]
        keywords = call_openai_chat(prompt, max_tokens=100)
        if keywords:
            cleaned = [k.strip() for k in keywords.replace("\n", ",").split(",") if k.strip()]
            if cleaned:
                return cleaned[:top_k]
    words = re.findall(r"[A-Za-z가-힣]{3,}", text.lower())
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_k]]


def generate_quizzes(text: str, count: int = 3) -> List[Dict[str, str]]:
    if OPENAI_API_KEY:
        prompt = [
            {
                "role": "system",
                "content": "학습 텍스트에서 객관식/주관식 혼합 문제를 JSON 리스트로 생성하세요. 각 항목은 question, answer, explanation 키를 포함합니다. 한국어로 작성하세요.",
            },
            {"role": "user", "content": f"문제 개수: {count}. 원문: {text[:8000]}"},
        ]
        completion = call_openai_chat(prompt, max_tokens=800)
        if completion:
            try:
                data = json.loads(completion)
                parsed = []
                for idx, item in enumerate(data[:count]):
                    parsed.append(
                        {
                            "id": idx + 1,
                            "question": item.get("question", ""),
                            "answer": item.get("answer", ""),
                            "explanation": item.get("explanation", ""),
                        }
                    )
                if parsed:
                    return parsed
            except json.JSONDecodeError:
                pass
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 10]
    quizzes = []
    keywords = extract_keywords(text, top_k=count * 2 or 6)
    for idx in range(min(count, len(sentences))):
        sentence = sentences[idx % len(sentences)]
        keyword = keywords[idx] if idx < len(keywords) else f"키워드{idx + 1}"
        question = sentence.replace(keyword, "____") if keyword in sentence else f"다음 문장을 요약하세요: {sentence}"
        quizzes.append(
            {
                "id": idx + 1,
                "question": question,
                "answer": keyword,
                "explanation": sentence,
            }
        )
    return quizzes


def build_json_response(data: Dict, status: int = 200) -> Tuple[int, Dict[str, str], bytes]:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    return status, headers, body


def parse_multipart(body: bytes, boundary: bytes) -> Dict[str, Tuple[Dict[str, str], bytes]]:
    boundary_marker = b"--" + boundary
    parts = body.split(boundary_marker)
    parsed: Dict[str, Tuple[Dict[str, str], bytes]] = {}
    for part in parts:
        if not part or part in (b"--", b"--\r\n"):
            continue
        part = part.strip(b"\r\n")
        if b"\r\n\r\n" not in part:
            continue
        header_raw, content = part.split(b"\r\n\r\n", 1)
        headers = {}
        for line in header_raw.split(b"\r\n"):
            if b":" in line:
                name, value = line.decode("latin-1").split(":", 1)
                headers[name.strip().lower()] = value.strip()
        disposition = headers.get("content-disposition", "")
        name_match = re.search(r'name="([^"]+)"', disposition)
        filename_match = re.search(r'filename="([^"]*)"', disposition)
        name = name_match.group(1) if name_match else "part"
        if filename_match:
            headers["filename"] = filename_match.group(1)
        parsed[name] = (headers, content)
    return parsed


def transcribe_file(filename: str, data: bytes) -> str:
    try:
        ext = os.path.splitext(filename)[1].lower()
        if ext in {".txt", ".md"}:
            return data.decode("utf-8", errors="ignore")
        if OPENAI_API_KEY:
            boundary = f"----WebKitFormBoundary{int(time.time() * 1000)}"
            body_parts = [
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode("utf-8"),
                data,
                b"\r\n",
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\n{OPENAI_TRANSCRIBE_MODEL}\r\n".encode("utf-8"),
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"response_format\"\r\n\r\ntext\r\n".encode("utf-8"),
                f"--{boundary}--\r\n".encode("utf-8"),
            ]
            body = b"".join(body_parts)
            request = urllib.request.Request(
                f"{OPENAI_API_BASE}/audio/transcriptions",
                data=body,
                headers={
                    "Content-Type": f"multipart/form-data; boundary={boundary}",
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=120) as resp:
                    return resp.read().decode("utf-8")
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
                pass
        return f"[STT 변환 예시] {filename}의 음성에서 추출된 텍스트입니다. (데모 모드)"
    except Exception:
        return "파일을 텍스트로 변환하지 못했습니다."


def handle_login(store: Dict, payload: Dict) -> Tuple[int, Dict[str, str], bytes]:
    username = payload.get("username")
    email = payload.get("email")
    password = payload.get("password")
    if not (username and email and password):
        return build_json_response({"error": "모든 필드가 필요합니다."}, status=400)

    existing = next((u for u in store["users"] if u["email"] == email), None)
    if existing:
        if existing.get("password") != password:
            return build_json_response({"error": "비밀번호가 일치하지 않습니다."}, status=401)
    else:
        store["users"].append({"username": username, "email": email, "password": password})
    save_store(store)
    return build_json_response({"message": "로그인 성공", "email": email})


def handle_folder(store: Dict, method: str, payload: Dict, email: str) -> Tuple[int, Dict[str, str], bytes]:
    if not email:
        return build_json_response({"error": "사용자 이메일이 필요합니다."}, status=400)

    if method == "POST":
        name = payload.get("name")
        parent = payload.get("parent_id")
        if not name:
            return build_json_response({"error": "폴더 이름이 필요합니다."}, status=400)
        folder_id = next_id(store, "folder")
        folder = {
            "id": folder_id,
            "name": name,
            "parent_id": parent,
            "owner": email,
        }
        store["folders"].append(folder)
        save_store(store)
        return build_json_response({"message": "폴더가 추가되었습니다.", "folder": folder}, status=201)

    if method == "PUT":
        folder_id = payload.get("id")
        new_name = payload.get("name")
        folder = next((f for f in store["folders"] if f["id"] == folder_id and f["owner"] == email), None)
        if not folder:
            return build_json_response({"error": "폴더를 찾을 수 없습니다."}, status=404)
        folder["name"] = new_name or folder["name"]
        save_store(store)
        return build_json_response({"message": "폴더가 수정되었습니다.", "folder": folder})

    if method == "DELETE":
        folder_id = payload.get("id")
        before = len(store["folders"])
        store["folders"] = [f for f in store["folders"] if not (f["id"] == folder_id and f["owner"] == email)]
        if len(store["folders"]) == before:
            return build_json_response({"error": "폴더를 찾을 수 없습니다."}, status=404)
        save_store(store)
        return build_json_response({"message": "폴더가 삭제되었습니다."}, status=204)

    return build_json_response({"error": "지원하지 않는 메서드입니다."}, status=405)


def handle_upload(store: Dict, headers: Dict[str, str], body: bytes, owner: str) -> Tuple[int, Dict[str, str], bytes]:
    content_type = headers.get("content-type", "")
    match = re.search(r"boundary=(.*)", content_type)
    if not match:
        return build_json_response({"error": "multipart/form-data 요청이 필요합니다."}, status=400)
    boundary = match.group(1).encode("latin-1")
    parts = parse_multipart(body, boundary)
    if "file" not in parts:
        return build_json_response({"error": "파일이 포함되어야 합니다."}, status=400)
    file_headers, file_data = parts["file"]
    filename = file_headers.get("filename", f"upload_{int(time.time())}")
    ensure_directories()
    file_id = next_id(store, "file")
    safe_name = f"{file_id}_{os.path.basename(filename)}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_data)

    text = transcribe_file(filename, file_data)
    summary = summarize_text(text)
    keywords = extract_keywords(text)
    quizzes = generate_quizzes(text)

    file_record = {
        "id": file_id,
        "name": filename,
        "path": file_path,
        "owner": owner,
        "text": text,
        "summary": summary,
        "keywords": keywords,
    }
    store["files"].append(file_record)
    for quiz in quizzes:
        quiz_id = next_id(store, "quiz")
        store["quizzes"].append({**quiz, "id": quiz_id, "file_id": file_id})
    save_store(store)

    return build_json_response({
        "message": "업로드 및 변환이 완료되었습니다.",
        "file": file_record,
        "quizzes": [q for q in store["quizzes"] if q["file_id"] == file_id],
    }, status=201)


def handle_analyze(store: Dict, payload: Dict) -> Tuple[int, Dict[str, str], bytes]:
    text = payload.get("text", "").strip()
    action_type = payload.get("type", "summary")
    count = int(payload.get("count", 3))
    if not text:
        return build_json_response({"error": "텍스트가 필요합니다."}, status=400)

    if action_type == "keyword":
        return build_json_response({"keywords": extract_keywords(text)})
    if action_type == "quiz":
        return build_json_response({"quizzes": generate_quizzes(text, count)})
    return build_json_response({"summary": summarize_text(text)})


def handle_file_list(store: Dict, email: str) -> Tuple[int, Dict[str, str], bytes]:
    files = [
        {
            "id": f["id"],
            "name": f["name"],
            "summary": f.get("summary", ""),
        }
        for f in store["files"]
        if not email or f.get("owner") == email
    ]
    return build_json_response({"files": files})


def serve_file(path: str) -> Tuple[int, Dict[str, str], bytes]:
    if not os.path.exists(path):
        return 404, {"Content-Type": "text/plain"}, b"Not Found"
    with open(path, "rb") as f:
        data = f.read()
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return 200, {"Content-Type": content_type}, data


class ThreadedHTTPServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.store = load_store()

    def handle_client(self, conn: socket.socket, addr: Tuple[str, int]) -> None:
        try:
            method, path, version, headers, body = parse_request(conn)
            if not method:
                send_response(conn, 400, {"Content-Type": "text/plain"}, b"Bad Request")
                return

            if method == "OPTIONS":
                send_response(conn, 204, {"Content-Type": "text/plain"})
                return

            if path == "/" or path == "/final_index.html":
                status, hdrs, data = serve_file("final_index.html")
                send_response(conn, status, hdrs, data)
                return

            if path.startswith("/api/login") and method == "POST":
                payload = json.loads(body.decode("utf-8")) if body else {}
                status, hdrs, data = handle_login(self.store, payload)
                send_response(conn, status, hdrs, data)
                return

            if path.startswith("/api/files") and method == "GET":
                email = ""
                if "?" in path:
                    _, query = path.split("?", 1)
                    for pair in query.split("&"):
                        if pair.startswith("email="):
                            email = pair.split("=", 1)[1]
                status, hdrs, data = handle_file_list(self.store, email)
                send_response(conn, status, hdrs, data)
                return

            if path.startswith("/api/folders"):
                email = ""
                if "?" in path:
                    _, query = path.split("?", 1)
                    for pair in query.split("&"):
                        if pair.startswith("email="):
                            email = pair.split("=", 1)[1]
                payload = json.loads(body.decode("utf-8")) if body else {}
                status, hdrs, data = handle_folder(self.store, method, payload, email)
                send_response(conn, status, hdrs, data)
                return

            if path.startswith("/api/upload") and method == "POST":
                owner = ""
                if "?" in path:
                    _, query = path.split("?", 1)
                    for pair in query.split("&"):
                        if pair.startswith("email="):
                            owner = pair.split("=", 1)[1]
                status, hdrs, data = handle_upload(self.store, headers, body, owner)
                send_response(conn, status, hdrs, data)
                return

            if path.startswith("/api/analyze") and method == "POST":
                payload = json.loads(body.decode("utf-8")) if body else {}
                status, hdrs, data = handle_analyze(self.store, payload)
                send_response(conn, status, hdrs, data)
                return

            send_response(conn, 404, {"Content-Type": "text/plain"}, b"Not Found")
        except Exception as exc:  # pragma: no cover - safety net
            error_msg = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
            send_response(conn, 500, {"Content-Type": "application/json"}, error_msg)
        finally:
            conn.close()

    def serve_forever(self) -> None:
        ensure_directories()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"[*] HTTP server listening on {self.host}:{self.port}")
            while True:
                conn, addr = server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()


def main() -> None:
    server = ThreadedHTTPServer(HOST, PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
