# client_gui.py
# 클라이언트 GUI 메인 파일 (기존 ai_learning_gui.py 리팩토링)

from tkinter import Tk
from Client.client_ui import ClientUI
from Client.client_core import TCPClient
from Client.client_handlers import ClientHandlers


class AILearningGUI:
    """AI 학습 지원 GUI 클라이언트"""
    
    def __init__(self, root):
        self.root = root
        
        # TCP 클라이언트
        self.tcp_client = TCPClient()
        
        # UI 구성
        self.ui = ClientUI(root)
        
        # 이벤트 핸들러
        self.handlers = ClientHandlers(self.ui, self.tcp_client)
        
        # UI에 root 참조 추가 (핸들러에서 사용)
        self.ui.root = root
        
        # 기본 사용자 설정 (로그인 없이)
        self.handlers.current_user_email = "user@example.com"
        self.ui.current_user_email = "user@example.com"
        self.ui.current_username = "user"
        self.ui.is_logged_in = True
        
        # 서버 자동 연결 및 파일 목록 로드
        self._auto_connect_server()
    
    def _auto_connect_server(self):
        """서버 자동 연결 및 파일 목록 로드"""
        from env_utils import DEFAULT_HOST, DEFAULT_PORT
        
        # UI 업데이트를 위해 after 사용
        def connect():
            if self.tcp_client.connect(DEFAULT_HOST, DEFAULT_PORT):
                self.ui.server_status_label.config(
                    text=f"연결 상태: 연결됨 ({DEFAULT_HOST}:{DEFAULT_PORT})", 
                    fg='green'
                )
                # 파일 목록 로드
                self.handlers.load_file_list()
            else:
                self.ui.server_status_label.config(
                    text=f"연결 상태: 연결 실패 ({DEFAULT_HOST}:{DEFAULT_PORT})", 
                    fg='red'
                )
        
        # UI가 완전히 로드된 후 연결 시도
        self.root.after(100, connect)


def main():
    root = Tk()
    app = AILearningGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

