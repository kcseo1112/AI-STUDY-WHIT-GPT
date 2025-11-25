# TCP_file_client.py
# TCP 파일 전송 GUI 클라이언트
import socket
import os
import sys
import threading
from tkinter import *
from tkinter import filedialog, messagebox, scrolledtext

HOST = ''  # 기본 서버 주소
PORT = 2501
BUFSIZE = 4096  # 파일 전송용 버퍼 크기 (4KB)

class TCPFileClient:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP 파일 전송 클라이언트")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        self.sock = None
        self.is_connected = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # 상단 프레임: 서버 연결 설정
        top_frame = Frame(self.root, padx=10, pady=10)
        top_frame.pack(fill=X)
        
        Label(top_frame, text="서버 주소:", font=("맑은 고딕", 10)).grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.host_entry = Entry(top_frame, width=20, font=("맑은 고딕", 10))
        self.host_entry.insert(0, HOST)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)
        
        Label(top_frame, text="포트:", font=("맑은 고딕", 10)).grid(row=0, column=2, sticky=W, padx=5, pady=5)
        self.port_entry = Entry(top_frame, width=10, font=("맑은 고딕", 10))
        self.port_entry.insert(0, str(PORT))
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)
        
        self.connect_btn = Button(top_frame, text="연결", command=self.connect_server, 
                                  bg="#4CAF50", fg="white", font=("맑은 고딕", 10, "bold"),
                                  width=8)
        self.connect_btn.grid(row=0, column=4, padx=5, pady=5)
        
        self.disconnect_btn = Button(top_frame, text="연결 해제", command=self.disconnect_server,
                                     bg="#f44336", fg="white", font=("맑은 고딕", 10, "bold"),
                                     width=8, state=DISABLED)
        self.disconnect_btn.grid(row=0, column=5, padx=5, pady=5)
        
        # 연결 상태 표시
        self.status_label = Label(top_frame, text="연결 안됨", fg="red", font=("맑은 고딕", 9))
        self.status_label.grid(row=1, column=0, columnspan=6, sticky=W, padx=5, pady=2)
        
        # 중간 프레임: 파일 선택 및 전송
        mid_frame = Frame(self.root, padx=10, pady=10)
        mid_frame.pack(fill=X)
        
        self.file_label = Label(mid_frame, text="선택된 파일: 없음", 
                                font=("맑은 고딕", 9), fg="gray", anchor=W)
        self.file_label.pack(fill=X, pady=5)
        
        btn_frame = Frame(mid_frame)
        btn_frame.pack(fill=X, pady=5)
        
        self.select_btn = Button(btn_frame, text="파일 선택", command=self.select_file,
                                 bg="#2196F3", fg="white", font=("맑은 고딕", 10, "bold"),
                                 width=12, state=DISABLED)
        self.select_btn.pack(side=LEFT, padx=5)
        
        self.send_btn = Button(btn_frame, text="파일 전송", command=self.send_file_thread,
                               bg="#FF9800", fg="white", font=("맑은 고딕", 10, "bold"),
                               width=12, state=DISABLED)
        self.send_btn.pack(side=LEFT, padx=5)
        
        # 진행률 표시
        self.progress_label = Label(mid_frame, text="", font=("맑은 고딕", 9))
        self.progress_label.pack(fill=X, pady=5)
        
        self.progress_bar = Label(mid_frame, text="", bg="#e0e0e0", height=2, anchor=W)
        self.progress_bar.pack(fill=X, pady=2)
        
        # 하단 프레임: 로그 출력
        log_frame = Frame(self.root, padx=10, pady=10)
        log_frame.pack(fill=BOTH, expand=True)
        
        Label(log_frame, text="로그:", font=("맑은 고딕", 10, "bold")).pack(anchor=W)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70,
                                                   font=("Consolas", 9), wrap=WORD)
        self.log_text.pack(fill=BOTH, expand=True, pady=5)
        
        self.selected_file_path = None
        
    def log(self, message):
        """로그 메시지 추가"""
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        self.root.update()
        
    def connect_server(self):
        """서버에 연결"""
        try:
            host = self.host_entry.get().strip() or HOST
            port = int(self.port_entry.get().strip() or PORT)
            
            self.log(f"서버 연결 시도: {host}:{port}")
            
            self.sock = socket.create_connection((host, port), timeout=10)
            self.is_connected = True
            
            self.status_label.config(text=f"연결됨: {host}:{port}", fg="green")
            self.connect_btn.config(state=DISABLED)
            self.disconnect_btn.config(state=NORMAL)
            self.select_btn.config(state=NORMAL)
            self.send_btn.config(state=NORMAL)
            self.host_entry.config(state=DISABLED)
            self.port_entry.config(state=DISABLED)
            
            self.log("✓ 서버 연결 성공!")
            
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            self.log(f"✗ 서버 연결 실패: {e}")
            messagebox.showerror("연결 오류", f"서버에 연결할 수 없습니다:\n{e}")
        except ValueError:
            self.log("✗ 잘못된 포트 번호입니다.")
            messagebox.showerror("입력 오류", "포트 번호는 숫자여야 합니다.")
            
    def disconnect_server(self):
        """서버 연결 해제"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        
        self.is_connected = False
        self.status_label.config(text="연결 안됨", fg="red")
        self.connect_btn.config(state=NORMAL)
        self.disconnect_btn.config(state=DISABLED)
        self.select_btn.config(state=DISABLED)
        self.send_btn.config(state=DISABLED)
        self.host_entry.config(state=NORMAL)
        self.port_entry.config(state=NORMAL)
        
        self.log("서버 연결 해제됨")
        
    def select_file(self):
        """파일 선택 대화상자"""
        file_path = filedialog.askopenfilename(
            title="전송할 파일 선택",
            filetypes=[("모든 파일", "*.*")]
        )
        
        if file_path:
            self.selected_file_path = file_path
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            size_mb = file_size / (1024 * 1024)
            
            self.file_label.config(text=f"선택된 파일: {filename} ({size_mb:.2f} MB)", fg="black")
            self.log(f"파일 선택: {filename} ({file_size:,} bytes)")
            
    def send_file_thread(self):
        """파일 전송을 별도 스레드에서 실행"""
        if not self.selected_file_path:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
            
        if not self.is_connected or not self.sock:
            messagebox.showwarning("경고", "서버에 연결되어 있지 않습니다.")
            return
        
        # UI 비활성화
        self.select_btn.config(state=DISABLED)
        self.send_btn.config(state=DISABLED)
        
        # 별도 스레드에서 전송 실행
        thread = threading.Thread(target=self.send_file, daemon=True)
        thread.start()
        
    def send_file(self):
        """서버로 파일 전송"""
        try:
            file_path = self.selected_file_path
            
            # 파일 존재 확인
            if not os.path.exists(file_path):
                self.log(f"✗ 오류: 파일을 찾을 수 없습니다: {file_path}")
                messagebox.showerror("오류", "파일을 찾을 수 없습니다.")
                return False
            
            # 파일 정보
            file_size = os.path.getsize(file_path)
            filename = os.path.basename(file_path)
            
            self.log(f"전송 시작: {filename} ({file_size:,} bytes)")
            
            # 1단계: 파일명 전송
            filename_bytes = filename.encode('utf-8')
            self.sock.sendall(filename_bytes + b'\0')
            self.log("파일명 전송 완료")
            
            # 2단계: 서버 준비 완료 신호 대기
            ready_signal = self.sock.recv(5)
            if ready_signal != b"READY":
                self.log("✗ 서버 준비 신호를 받지 못했습니다.")
                messagebox.showerror("오류", "서버 준비 신호를 받지 못했습니다.")
                return False
            self.log("서버 준비 완료")
            
            # 3단계: 파일 크기 전송
            file_size_str = str(file_size).encode('utf-8')
            self.sock.sendall(file_size_str + b'\0')
            self.log("파일 크기 전송 완료")
            
            # 4단계: 파일 데이터 전송
            sent_size = 0
            with open(file_path, 'rb') as f:
                while sent_size < file_size:
                    chunk = f.read(BUFSIZE)
                    if not chunk:
                        break
                    self.sock.sendall(chunk)
                    sent_size += len(chunk)
                    
                    # 진행률 업데이트
                    progress = (sent_size / file_size) * 100
                    progress_text = f"전송 진행률: {progress:.1f}% ({sent_size:,}/{file_size:,} bytes)"
                    self.progress_label.config(text=progress_text)
                    
                    # 진행률 바 업데이트
                    bar_width = int((sent_size / file_size) * 100)
                    bar_text = "█" * bar_width + "░" * (100 - bar_width)
                    self.progress_bar.config(text=bar_text[:100])
                    
                    self.root.update()
            
            self.log("파일 데이터 전송 완료")
            
            # 5단계: 서버 응답 확인
            response = self.sock.recv(7)
            if response == b"SUCCESS":
                self.log("✓ 서버에서 파일 수신 완료 확인")
                self.progress_label.config(text="전송 완료!")
                self.progress_bar.config(text="█" * 100)
                messagebox.showinfo("성공", "파일 전송이 완료되었습니다!")
                return True
            elif response == b"ERROR":
                self.log("✗ 서버에서 오류 발생")
                messagebox.showerror("오류", "서버에서 오류가 발생했습니다.")
                return False
            else:
                self.log(f"✗ 알 수 없는 서버 응답: {response}")
                messagebox.showerror("오류", f"알 수 없는 서버 응답: {response}")
                return False
                
        except Exception as e:
            self.log(f"✗ 파일 전송 중 오류 발생: {e}")
            messagebox.showerror("오류", f"파일 전송 중 오류가 발생했습니다:\n{e}")
            return False
        finally:
            # UI 활성화
            self.select_btn.config(state=NORMAL)
            self.send_btn.config(state=NORMAL)
            self.progress_label.config(text="")
            self.progress_bar.config(text="")

def main():
    # 명령줄 인자로 파일 경로가 제공된 경우 (기존 방식 지원)
    if len(sys.argv) >= 2:
        file_path = sys.argv[1]
        server_host = sys.argv[2] if len(sys.argv) > 2 else HOST
        server_port = int(sys.argv[3]) if len(sys.argv) > 3 else PORT
        
        try:
            with socket.create_connection((server_host, server_port), timeout=10) as s:
                print(f"서버에 연결됨: {server_host}:{server_port}")
                
                # 간단한 전송 함수 (GUI 없이)
                def send_file_simple(sock, file_path):
                    try:
                        if not os.path.exists(file_path):
                            print(f"오류: 파일을 찾을 수 없습니다: {file_path}")
                            return False
                        
                        file_size = os.path.getsize(file_path)
                        filename = os.path.basename(file_path)
                        
                        print(f"전송할 파일: {filename}")
                        print(f"파일 크기: {file_size} bytes")
                        
                        filename_bytes = filename.encode('utf-8')
                        sock.sendall(filename_bytes + b'\0')
                        
                        ready_signal = sock.recv(5)
                        if ready_signal != b"READY":
                            print("서버 준비 신호를 받지 못했습니다.")
                            return False
                        
                        file_size_str = str(file_size).encode('utf-8')
                        sock.sendall(file_size_str + b'\0')
                        
                        sent_size = 0
                        with open(file_path, 'rb') as f:
                            while sent_size < file_size:
                                chunk = f.read(BUFSIZE)
                                if not chunk:
                                    break
                                sock.sendall(chunk)
                                sent_size += len(chunk)
                                progress = (sent_size / file_size) * 100
                                print(f"\r전송 진행률: {progress:.1f}% ({sent_size}/{file_size} bytes)", end='', flush=True)
                        
                        print("\n파일 데이터 전송 완료")
                        
                        response = sock.recv(7)
                        if response == b"SUCCESS":
                            print("서버에서 파일 수신 완료 확인")
                            return True
                        else:
                            print(f"알 수 없는 서버 응답: {response}")
                            return False
                            
                    except Exception as e:
                        print(f"\n파일 전송 중 오류 발생: {e}")
                        return False
                
                if send_file_simple(s, file_path):
                    print("\n파일 전송 성공!")
                else:
                    print("\n파일 전송 실패!")
                    
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            print(f"서버에 연결할 수 없습니다: {e}")
        except KeyboardInterrupt:
            print("\n사용자 취소로 종료합니다.")
    else:
        # GUI 모드
        root = Tk()
        app = TCPFileClient(root)
        root.mainloop()

if __name__ == "__main__":
    main()
