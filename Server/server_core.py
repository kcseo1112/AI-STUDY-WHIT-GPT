# server_core.py
# 서버 핵심 기능 (TCP 소켓, 클라이언트 연결 관리)

import socket
import json
import threading
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env_utils import DEFAULT_HOST, DEFAULT_PORT, BUFSIZE, RECEIVE_DIR
try:
    from Server.server_data_supabase import ServerDataManager
except ImportError:
    from Server.server_data import ServerDataManager
from Server.server_handlers import ServerCommandHandlers


class AILearningServer:
    """AI 학습 지원 서버"""
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, log_callback=None):
        self.host = host
        self.port = port
        self.server_socket = None
        self.is_running = False
        self.log_callback = log_callback
        self.connected_clients = {}
        
        # 데이터 관리자 및 핸들러 초기화
        self.data_manager = ServerDataManager()
        self.handlers = ServerCommandHandlers(self.data_manager, log_callback)
        
        # 디렉토리 생성
        os.makedirs(RECEIVE_DIR, exist_ok=True)
    
    def _log(self, message):
        """로그 출력 (콘솔 또는 GUI)"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    def start(self):
        """서버 시작"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.is_running = True
            
            self._log(f"AI 학습 지원 서버 시작됨")
            self._log(f"주소: {self.host}:{self.port}")
            self._log(f"대기 중...")
            
            while self.is_running:
                try:
                    self.server_socket.settimeout(1.0)
                    conn, addr = self.server_socket.accept()
                    client_id = f"{addr[0]}:{addr[1]}"
                    self.connected_clients[client_id] = addr
                    self._log(f"\n[연결] 클라이언트 연결: {client_id}")
                    if self.log_callback:
                        self.log_callback(f"[연결] 클라이언트: {client_id}")
                    
                    # 각 클라이언트를 별도 스레드에서 처리
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(conn, addr),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except OSError as e:
                    if self.is_running:
                        print(f"서버 소켓 오류 발생: {e}")
                    break
                    
        except Exception as e:
            print(f"서버 오류: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
    
    def stop(self):
        """서버 중지"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        print("서버가 중지되었습니다.")
    
    def handle_client(self, conn, addr):
        """클라이언트 요청 처리"""
        try:
            with conn:
                # STT 처리는 OpenAI API 호출로 시간이 걸릴 수 있으므로 타임아웃 증가
                conn.settimeout(300.0)  # 5분 타임아웃 (STT 처리 시간 고려)
                
                # 먼저 4바이트를 읽어서 명령 메시지인지 확인
                length_bytes = conn.recv(4, socket.MSG_PEEK)
                
                if len(length_bytes) == 4:
                    # 4바이트가 모두 0-255 범위의 숫자이고 합리적인 크기면 명령일 가능성
                    try:
                        message_length = int.from_bytes(length_bytes, byteorder='big')
                        # 명령 메시지는 보통 1KB 이하이므로, 100KB 이하면 명령으로 간주
                        if message_length > 0 and message_length < 100000:
                            # 명령 전송 처리
                            self.handle_command(conn)
                            return
                    except:
                        pass
                
                # 파일 전송 처리 (기존 프로토콜)
                self.receive_file(conn)
                        
        except socket.timeout:
            # 타임아웃은 정상 (연결 유지 확인)
            pass
        except Exception as e:
            self._log(f"[오류] 클라이언트 처리 오류 ({addr}): {e}")
        finally:
            client_id = f"{addr[0]}:{addr[1]}"
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            self._log(f"[종료] 클라이언트 연결 종료: {client_id}")
    
    def handle_command(self, conn):
        """명령 메시지 처리"""
        try:
            # STT 처리를 위해 타임아웃 증가
            conn.settimeout(300.0)  # 5분 타임아웃
            
            # 메시지 길이 수신 (4바이트)
            length_bytes = conn.recv(4)
            if len(length_bytes) != 4:
                return
            
            message_length = int.from_bytes(length_bytes, byteorder='big')
            
            # 메시지 본문 수신
            message_data = b""
            while len(message_data) < message_length:
                chunk = conn.recv(min(BUFSIZE, message_length - len(message_data)))
                if not chunk:
                    return
                message_data += chunk
            
            if len(message_data) < message_length:
                return
            
            # JSON 파싱
            try:
                message = json.loads(message_data.decode('utf-8'))
                command = message.get("command")
                data = message.get("data", {})
                
                # 명령 처리
                response = self.process_command(command, data, conn)
                
                # 응답 전송
                response_json = json.dumps(response, ensure_ascii=False)
                response_bytes = response_json.encode('utf-8')
                response_length = len(response_bytes)
                
                conn.sendall(response_length.to_bytes(4, byteorder='big'))
                conn.sendall(response_bytes)
                
            except json.JSONDecodeError as e:
                response = {"status": "error", "message": f"JSON 파싱 오류: {e}"}
                response_json = json.dumps(response, ensure_ascii=False)
                response_bytes = response_json.encode('utf-8')
                conn.sendall(len(response_bytes).to_bytes(4, byteorder='big'))
                conn.sendall(response_bytes)
        except Exception as e:
            print(f"명령 처리 오류: {e}")
    
    def process_command(self, command, data, conn):
        """명령 처리 라우팅"""
        try:
            if command == "login":
                return self.handlers.handle_login(data)
            elif command == "convert_audio":
                return self.handlers.handle_convert_audio(data)
            elif command == "save_text":
                return self.handlers.handle_save_text(data)
            elif command == "manage_folder":
                return self.handlers.handle_manage_folder(data)
            elif command == "load_file":
                return self.handlers.handle_load_file(data)
            elif command == "save_score":
                return self.handlers.handle_save_score(data)
            elif command == "generate_quiz":
                return self.handlers.handle_generate_quiz(data)
            elif command == "generate_single_quiz":
                return self.handlers.handle_generate_single_quiz(data)
            elif command == "load_quizzes":
                return self.handlers.handle_load_quizzes(data)
            elif command == "list_files":
                return self.handlers.handle_list_files(data)
            elif command == "analyze_text":
                return self.handlers.handle_analyze_text(data)
            else:
                return {"status": "error", "message": f"알 수 없는 명령: {command}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def receive_file(self, conn):
        """파일 수신 (기존 프로토콜)"""
        try:
            # 파일명 수신
            filename_data = b""
            while True:
                chunk = conn.recv(1)
                if not chunk:
                    return False
                if chunk == b'\0':
                    break
                filename_data += chunk
            
            try:
                filename = filename_data.decode('utf-8')
            except UnicodeDecodeError:
                filename = filename_data.decode('latin-1', errors='ignore')
            
            if not filename:
                return False
            
            print(f"파일 수신 시작: {filename}")
            
            # 준비 신호 전송
            conn.sendall(b"READY")
            
            # 파일 크기 수신
            file_size_data = b""
            while True:
                chunk = conn.recv(1)
                if not chunk:
                    return False
                if chunk == b'\0':
                    break
                file_size_data += chunk
            
            try:
                file_size_str = file_size_data.decode('utf-8')
                file_size = int(file_size_str)
            except ValueError:
                return False
            
            # 파일 데이터 수신
            file_path = os.path.join(RECEIVE_DIR, os.path.basename(filename))
            received_size = 0
            
            with open(file_path, 'wb') as f:
                while received_size < file_size:
                    remaining = file_size - received_size
                    chunk_size = min(BUFSIZE, remaining)
                    data = conn.recv(chunk_size)
                    if not data:
                        return False
                    f.write(data)
                    received_size += len(data)
            
            print(f"파일 수신 완료: {file_path}")
            
            # 성공 신호 전송
            conn.sendall(b"SUCCESS")
            return True
            
        except Exception as e:
            print(f"파일 수신 오류: {e}")
            try:
                conn.sendall(b"ERROR")
            except:
                pass
            return False

