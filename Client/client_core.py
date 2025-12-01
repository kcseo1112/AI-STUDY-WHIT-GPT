# client_core.py
# 클라이언트 TCP 통신 모듈

import json
import socket
import threading
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env_utils import DEFAULT_HOST, DEFAULT_PORT, BUFSIZE


class TCPClient:
    """TCP/IP 소켓 클라이언트 (요청당 새 연결 방식)"""

    def __init__(self):
        self.lock = threading.Lock()
        self.is_connected = False
        self.host = None
        self.port = None

    def connect(self, host, port):
        """서버 연결 테스트 후 호스트/포트만 기억"""
        try:
            # 한 번만 테스트 연결
            with socket.create_connection((host, port), timeout=5):
                pass
            with self.lock:
                self.host = host
                self.port = port
                self.is_connected = True
            return True
        except Exception as e:
            print(f"연결 실패: {e}")
            return False

    def disconnect(self):
        """서버 연결 해제 (논리적 연결만 해제)"""
        with self.lock:
            self.host = None
            self.port = None
            self.is_connected = False

    def _ensure_target(self):
        if not self.is_connected or not self.host or not self.port:
            raise RuntimeError("서버에 연결되어 있지 않습니다.")

    def send_command(self, command, data=None):
        """서버에 명령 전송 (요청당 새 소켓 사용)"""
        try:
            self._ensure_target()
        except RuntimeError as e:
            return {"status": "error", "message": str(e)}

        try:
            payload = {
                "command": command,
                "data": data or {}
            }
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            header = len(body).to_bytes(4, byteorder="big")

            with self.lock:
                # STT 처리는 OpenAI API 호출로 시간이 걸릴 수 있으므로 타임아웃 증가
                with socket.create_connection((self.host, self.port), timeout=300) as sock:
                    # 전송
                    sock.sendall(header)
                    sock.sendall(body)

                    # 응답 수신 (STT 처리 시간 고려하여 타임아웃 증가)
                    sock.settimeout(300.0)  # 5분 타임아웃
                    length_bytes = sock.recv(4)
                    if len(length_bytes) != 4:
                        return {"status": "error", "message": "응답 길이 수신 실패"}

                    resp_len = int.from_bytes(length_bytes, byteorder="big")
                    resp_data = b""
                    while len(resp_data) < resp_len:
                        chunk = sock.recv(min(BUFSIZE, resp_len - len(resp_data)))
                        if not chunk:
                            break
                        resp_data += chunk

            if len(resp_data) < resp_len:
                return {"status": "error", "message": "응답 데이터 부족"}

            return json.loads(resp_data.decode("utf-8"))

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def send_file(self, file_path):
        """파일 전송 (요청당 새 소켓 사용)"""
        try:
            self._ensure_target()
        except RuntimeError as e:
            return {"status": "error", "message": str(e)}

        try:
            if not os.path.exists(file_path):
                return {"status": "error", "message": "파일을 찾을 수 없습니다."}

            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)

            with self.lock:
                # 파일 전송은 큰 파일도 고려하여 타임아웃 증가
                with socket.create_connection((self.host, self.port), timeout=300) as sock:
                    sock.settimeout(300.0)  # 5분 타임아웃
                    # 파일명 전송
                    filename_bytes = filename.encode('utf-8')
                    sock.sendall(filename_bytes + b'\0')

                    # 서버 준비 신호 대기
                    ready_signal = sock.recv(5)
                    if ready_signal != b"READY":
                        return {"status": "error", "message": "서버 준비 신호를 받지 못했습니다."}

                    # 파일 크기 전송
                    file_size_str = str(file_size).encode('utf-8')
                    sock.sendall(file_size_str + b'\0')

                    # 파일 데이터 전송
                    sent_size = 0
                    with open(file_path, 'rb') as f:
                        while sent_size < file_size:
                            chunk = f.read(BUFSIZE)
                            if not chunk:
                                break
                            sock.sendall(chunk)
                            sent_size += len(chunk)

                    # 서버 응답 확인
                    response = sock.recv(7)
                    if response == b"SUCCESS":
                        return {"status": "success", "message": "파일 전송 완료"}
                    else:
                        return {"status": "error", "message": "서버에서 오류 발생"}

        except Exception as e:
            return {"status": "error", "message": str(e)}


