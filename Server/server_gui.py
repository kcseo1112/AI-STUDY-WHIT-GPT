# server_gui.py
# 서버 GUI (기존 ai_learning_server_gui.py 리팩토링)

import threading
import tkinter as tk
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tkinter import ttk, scrolledtext, messagebox

from Server.server_core import AILearningServer
from env_utils import DEFAULT_HOST, DEFAULT_PORT


class ServerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AI 학습 지원 서버")
        self.root.geometry("900x700")

        self.server: AILearningServer | None = None
        self.server_thread: threading.Thread | None = None
        self.connected_clients = {}  # 연결된 클라이언트 추적

        self._create_widgets()

    def _create_widgets(self):
        top = ttk.LabelFrame(self.root, text="서버 설정")
        top.pack(fill="x", padx=10, pady=10)

        ttk.Label(top, text="호스트").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.host_entry = ttk.Entry(top, width=18)
        self.host_entry.insert(0, DEFAULT_HOST)
        self.host_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(top, text="포트").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.port_entry = ttk.Entry(top, width=8)
        self.port_entry.insert(0, str(DEFAULT_PORT))
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)

        self.start_btn = ttk.Button(top, text="서버 시작", command=self.start_server)
        self.start_btn.grid(row=0, column=4, padx=5, pady=5)

        self.stop_btn = ttk.Button(top, text="서버 중지", command=self.stop_server, state="disabled")
        self.stop_btn.grid(row=0, column=5, padx=5, pady=5)

        self.status_label = ttk.Label(top, text="상태: 중지됨", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=6, padx=5, pady=5, sticky="w")

        # 로그 영역
        log_frame = ttk.LabelFrame(self.root, text="서버 로그")
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=20, width=80, state="disabled", font=("Consolas", 9)
        )
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # 클라이언트 연결 정보
        client_frame = ttk.LabelFrame(self.root, text="연결된 클라이언트")
        client_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.client_listbox = tk.Listbox(client_frame, height=4, font=("Consolas", 9))
        self.client_listbox.pack(fill="x", padx=5, pady=5)
        
        self.client_count_label = ttk.Label(client_frame, text="접속 클라이언트: 0명")
        self.client_count_label.pack(side="left", padx=5, pady=5)

    # --- 서버 제어 ---

    def start_server(self):
        if self.server_thread and self.server_thread.is_alive():
            messagebox.showinfo("알림", "이미 서버가 실행 중입니다.")
            return

        host = self.host_entry.get().strip() or DEFAULT_HOST
        try:
            port = int(self.port_entry.get().strip() or DEFAULT_PORT)
        except ValueError:
            messagebox.showerror("오류", "포트는 숫자여야 합니다.")
            return

        self.server = AILearningServer(host=host, port=port, log_callback=self._log)

        def run_server():
            self._log(f"[서버] 시작: {host}:{port}")
            self._set_status(running=True, host=host, port=port)
            try:
                self.server.start()
            finally:
                self._set_status(running=False)
                self._log("[서버] 중지됨")
                self._update_client_list()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

    def stop_server(self):
        if self.server:
            self.server.stop()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    # --- UI 업데이트 ---

    def _log(self, msg: str):
        def append():
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
            
            # 클라이언트 연결/종료 메시지 파싱
            if "[연결] 클라이언트:" in msg:
                parts = msg.split("클라이언트:")
                if len(parts) > 1:
                    client_id = parts[1].strip()
                    self.connected_clients[client_id] = client_id
                    self._update_client_list()
            elif "[종료] 클라이언트 연결 종료:" in msg:
                parts = msg.split("클라이언트 연결 종료:")
                if len(parts) > 1:
                    client_id = parts[1].strip()
                    if client_id in self.connected_clients:
                        del self.connected_clients[client_id]
                    self._update_client_list()

        self.root.after(0, append)
    
    def _update_client_list(self):
        """연결된 클라이언트 목록 업데이트"""
        def update():
            self.client_listbox.delete(0, tk.END)
            for client_id in self.connected_clients.values():
                self.client_listbox.insert(tk.END, client_id)
            self.client_count_label.config(text=f"접속 클라이언트: {len(self.connected_clients)}명")
        
        self.root.after(0, update)

    def _set_status(self, running: bool, host: str | None = None, port: int | None = None):
        def update():
            if running:
                self.status_label.config(
                    text=f"상태: 실행 중 ({host}:{port})", foreground="green"
                )
            else:
                self.status_label.config(text="상태: 중지됨", foreground="red")

        self.root.after(0, update)


def main():
    root = tk.Tk()
    app = ServerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

