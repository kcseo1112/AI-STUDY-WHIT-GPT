# client_ui.py
# 클라이언트 UI 구성 모듈

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tkinter import *
from tkinter import ttk, scrolledtext
from tkinter.font import Font
from env_utils import DEFAULT_HOST, DEFAULT_PORT


class ClientUI:
    """클라이언트 UI 구성 클래스"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AI 학습 지원 도구")
        self.root.geometry("1400x820")
        self.root.minsize(1300, 780)
        self.root.configure(bg='#f5f5f5')
        
        # 폰트 설정
        self.title_font = Font(family="맑은 고딕", size=18, weight="bold")
        self.heading_font = Font(family="맑은 고딕", size=12, weight="bold")
        self.normal_font = Font(family="맑은 고딕", size=10)
        
        # 로그인 상태
        self.is_logged_in = False
        self.current_user_email = None
        self.current_username = None
        
        # UI 구성
        self.create_widgets()
    
    def create_widgets(self):
        """위젯 생성"""
        # 메인 컨테이너
        main_container = Frame(self.root, bg='#f5f5f5')
        main_container.pack(fill=BOTH, expand=True)
        
        # 사이드바
        self.create_sidebar(main_container)
        
        # 메인 콘텐츠 영역
        self.create_main_content(main_container)
    
    def create_sidebar(self, parent):
        """사이드바 생성"""
        sidebar = Frame(parent, bg='#ffffff', width=300)
        sidebar.pack(side=LEFT, fill=Y, padx=0, pady=0)
        sidebar.pack_propagate(False)
        
        # 사이드바 헤더
        header = Frame(sidebar, bg='#333333', height=80)
        header.pack(fill=X)
        Label(header, text="🚀 AI 학습 지원 도구", font=self.title_font,
              bg='#333333', fg='white').pack(pady=20)
        
        # 서버 연결 설정 (자동 연결, UI는 읽기 전용)
        server_frame = LabelFrame(sidebar, text="🔌 서버 연결", font=self.heading_font,
                                  bg='#ffffff', fg='#333', padx=15, pady=10)
        server_frame.pack(fill=X, padx=10, pady=10)
        
        # 서버 정보 표시 (읽기 전용)
        Label(server_frame, text="서버 주소:", font=self.normal_font, bg='#ffffff').pack(anchor=W)
        self.server_host_label = Label(server_frame, text=DEFAULT_HOST,
                                       font=self.normal_font, bg='#ffffff', fg='#333')
        self.server_host_label.pack(anchor=W, pady=2)
        
        Label(server_frame, text="포트:", font=self.normal_font, bg='#ffffff').pack(anchor=W, pady=(5,0))
        self.server_port_label = Label(server_frame, text=str(DEFAULT_PORT),
                                        font=self.normal_font, bg='#ffffff', fg='#333')
        self.server_port_label.pack(anchor=W, pady=2)
        
        self.server_status_label = Label(server_frame, text="연결 상태: 연결 중...", 
                                         font=self.normal_font, bg='#ffffff', fg='#666')
        self.server_status_label.pack(pady=10)
        
        # AI 액션 메뉴
        action_frame = LabelFrame(sidebar, text="🎯 AI 액션 메뉴", font=self.heading_font,
                                  bg='#ffffff', fg='#333', padx=15, pady=10)
        action_frame.pack(fill=X, padx=10, pady=10)
        
        self.convert_btn = Button(action_frame, text="🎙️ 녹음 파일 변환",
               bg='#333333', fg='white', font=self.normal_font, relief=FLAT, pady=10)
        self.convert_btn.pack(fill=X)
        
        # 폴더 관리
        folder_frame = LabelFrame(sidebar, text="📁 폴더 관리", font=self.heading_font,
                                   bg='#ffffff', fg='#333', padx=15, pady=10)
        folder_frame.pack(fill=X, padx=10, pady=10)
        
        self.folder_btn = Button(folder_frame, text="📁 폴더 관리",
               bg='#333333', fg='white', font=self.normal_font, relief=FLAT, pady=10)
        self.folder_btn.pack(fill=X)
        
        # 프로젝트 기록
        history_frame = LabelFrame(sidebar, text="📚 프로젝트 기록", font=self.heading_font,
                                    bg='#ffffff', fg='#333', padx=15, pady=10)
        history_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 트리뷰로 프로젝트 표시
        self.project_tree = ttk.Treeview(history_frame, show='tree')
        self.project_tree.pack(fill=BOTH, expand=True)
        # 루트 노드 (변환된 파일)
        self.project_root = self.project_tree.insert('', 'end', text='변환된 파일', open=True)
    
    def create_main_content(self, parent):
        """메인 콘텐츠 영역 생성"""
        main_content = Frame(parent, bg='#ffffff')
        main_content.pack(side=LEFT, fill=BOTH, expand=True, padx=30, pady=30)
        
        # 문서 뷰어 컨테이너
        viewer_frame = Frame(main_content, bg='#ffffff')
        viewer_frame.pack(fill=BOTH, expand=True)
        
        # 문서 헤더
        self.document_header = Frame(viewer_frame, bg='#ffffff')
        self.document_header.pack(fill=X, pady=(0, 20))
        
        self.document_title = Label(self.document_header, text="AI 학습 지원 도구",
                                    font=self.title_font, bg='#ffffff', fg='#333')
        self.document_title.pack(anchor=W)
        
        # 인덱스 버튼
        self.index_frame = Frame(viewer_frame, bg='#ffffff')
        self.index_frame.pack(fill=X, pady=(0, 20))
        self.index_frame.pack_forget()
        
        self.summary_btn = Button(self.index_frame, text="📝 요약 정리",
                                  bg='#333333', fg='white', font=self.normal_font, relief=FLAT, padx=20, pady=10)
        self.summary_btn.pack(side=LEFT, padx=5)
        
        self.quiz_btn = Button(self.index_frame, text="❓ 퀴즈",
                                bg='#f0f0f0', fg='#666', font=self.normal_font, relief=FLAT, padx=20, pady=10)
        self.quiz_btn.pack(side=LEFT, padx=5)
        
        # 콘텐츠 영역 (스크롤 가능)
        self.content_canvas = Canvas(viewer_frame, bg='#ffffff', highlightthickness=0)
        scrollbar = Scrollbar(viewer_frame, orient="vertical", command=self.content_canvas.yview)
        self.content_frame = Frame(self.content_canvas, bg='#ffffff')
        
        self.content_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Canvas의 너비에 맞춰 content_frame이 확장되도록 설정
        self.content_window = self.content_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        def _update_content_canvas(event):
            # Canvas 너비에 맞춰 content_frame 너비 조정
            canvas_width = event.width
            self.content_canvas.itemconfig(self.content_window, width=canvas_width)
            self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))
        
        self.content_canvas.bind("<Configure>", _update_content_canvas)
        self.content_frame.bind("<Configure>", lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")))
        
        # 액션 폼들
        self.create_convert_form()
        self.create_folder_form()
        self.create_summary_section()
        self.create_quiz_section()
    
    def create_convert_form(self):
        """녹음 파일 변환 폼"""
        self.convert_frame = LabelFrame(self.content_frame, text="🎙️ 녹음 파일 변환",
                                        font=self.heading_font, bg='#ffffff', padx=25, pady=25)
        self.convert_frame.pack(fill=X, pady=10)
        self.convert_frame.pack_forget()
        
        Label(self.convert_frame, text="로컬 파일을 서버로 전송하여 텍스트로 변환하고 새로운 기록으로 저장합니다.",
              font=self.normal_font, bg='#ffffff', fg='#666', wraplength=800).pack(anchor=W, pady=10)
        
        file_frame = Frame(self.convert_frame, bg='#ffffff')
        file_frame.pack(fill=X, pady=10)
        
        self.audio_file_label = Label(file_frame, text="선택된 파일: 없음",
                                       font=self.normal_font, bg='#ffffff', fg='#666')
        self.audio_file_label.pack(anchor=W, pady=5)
        
        self.select_file_btn = Button(file_frame, text="파일 선택",
               bg='#2196F3', fg='white', font=self.normal_font, relief=FLAT, padx=15, pady=5)
        self.select_file_btn.pack(side=LEFT, padx=5)
        
        self.convert_btn_main = Button(self.convert_frame, text="📤 텍스트로 변환 및 문서 저장",
               bg='#333333', fg='white', font=self.normal_font, relief=FLAT, padx=20, pady=10)
        self.convert_btn_main.pack(pady=10)
        
        self.convert_result_label = Label(self.convert_frame, text="", font=self.normal_font,
                                          bg='#ffffff', fg='green', wraplength=800, justify=LEFT)
        self.convert_result_label.pack(anchor=W, pady=10)
    
    def create_folder_form(self):
        """폴더 관리 폼"""
        self.folder_frame = LabelFrame(self.content_frame, text="📁 폴더 관리",
                                       font=self.heading_font, bg='#ffffff', padx=25, pady=25)
        self.folder_frame.pack(fill=X, pady=10)
        self.folder_frame.pack_forget()
        
        # 탭 버튼
        tab_frame = Frame(self.folder_frame, bg='#ffffff')
        tab_frame.pack(fill=X, pady=(0, 20))
        
        self.folder_tab_add = Button(tab_frame, text="➕ 폴더 추가",
                                      bg='#333333', fg='white', font=self.normal_font, relief=FLAT, padx=15, pady=8)
        self.folder_tab_add.pack(side=LEFT, padx=5)
        
        self.folder_tab_update = Button(tab_frame, text="✏️ 폴더 수정",
                                        bg='#f0f0f0', fg='#666', font=self.normal_font, relief=FLAT, padx=15, pady=8)
        self.folder_tab_update.pack(side=LEFT, padx=5)
        
        self.folder_tab_delete = Button(tab_frame, text="🗑️ 폴더 삭제",
                                        bg='#f0f0f0', fg='#666', font=self.normal_font, relief=FLAT, padx=15, pady=8)
        self.folder_tab_delete.pack(side=LEFT, padx=5)
        
        # 폴더 추가 섹션
        self.folder_add_section = Frame(self.folder_frame, bg='#ffffff')
        self.folder_add_section.pack(fill=X, pady=10)
        
        Label(self.folder_add_section, text="폴더 이름:", font=self.normal_font, bg='#ffffff').pack(anchor=W, pady=5)
        self.folder_name_add_entry = Entry(self.folder_add_section, font=self.normal_font, width=50)
        self.folder_name_add_entry.pack(fill=X, pady=5)
        
        self.folder_add_btn = Button(self.folder_add_section, text="📤 폴더 추가",
               bg='#333333', fg='white', font=self.normal_font, relief=FLAT, padx=20, pady=8)
        self.folder_add_btn.pack(pady=10)
        
        self.folder_add_result = Label(self.folder_add_section, text="", font=self.normal_font,
                                       bg='#ffffff', fg='green', wraplength=800, justify=LEFT)
        self.folder_add_result.pack(anchor=W, pady=5)
        
        # 폴더 수정 섹션
        self.folder_update_section = Frame(self.folder_frame, bg='#ffffff')
        self.folder_update_section.pack(fill=X, pady=10)
        self.folder_update_section.pack_forget()
        
        Label(self.folder_update_section, text="기존 폴더 이름:", font=self.normal_font, bg='#ffffff').pack(anchor=W, pady=5)
        self.folder_name_old_entry = Entry(self.folder_update_section, font=self.normal_font, width=50)
        self.folder_name_old_entry.pack(fill=X, pady=5)
        
        Label(self.folder_update_section, text="새 폴더 이름:", font=self.normal_font, bg='#ffffff').pack(anchor=W, pady=5)
        self.folder_name_new_entry = Entry(self.folder_update_section, font=self.normal_font, width=50)
        self.folder_name_new_entry.pack(fill=X, pady=5)
        
        self.folder_update_btn = Button(self.folder_update_section, text="📤 폴더 수정",
               bg='#333333', fg='white', font=self.normal_font, relief=FLAT, padx=20, pady=8)
        self.folder_update_btn.pack(pady=10)
        
        self.folder_update_result = Label(self.folder_update_section, text="", font=self.normal_font,
                                          bg='#ffffff', fg='green', wraplength=800, justify=LEFT)
        self.folder_update_result.pack(anchor=W, pady=5)
        
        # 폴더 삭제 섹션
        self.folder_delete_section = Frame(self.folder_frame, bg='#ffffff')
        self.folder_delete_section.pack(fill=X, pady=10)
        self.folder_delete_section.pack_forget()
        
        Label(self.folder_delete_section, text="폴더 이름:", font=self.normal_font, bg='#ffffff').pack(anchor=W, pady=5)
        self.folder_name_delete_entry = Entry(self.folder_delete_section, font=self.normal_font, width=50)
        self.folder_name_delete_entry.pack(fill=X, pady=5)
        
        self.folder_delete_btn = Button(self.folder_delete_section, text="📤 폴더 삭제",
               bg='#f44336', fg='white', font=self.normal_font, relief=FLAT, padx=20, pady=8)
        self.folder_delete_btn.pack(pady=10)
        
        self.folder_delete_result = Label(self.folder_delete_section, text="", font=self.normal_font,
                                          bg='#ffffff', fg='green', wraplength=800, justify=LEFT)
        self.folder_delete_result.pack(anchor=W, pady=5)
    
    def create_summary_section(self):
        """요약 정리 섹션"""
        self.summary_frame = LabelFrame(self.content_frame, text="🔑 주요 키워드 및 핵심 요약",
                                        font=self.heading_font, bg='#ffffff', padx=25, pady=25)
        self.summary_frame.pack(fill=BOTH, expand=True, pady=10)
        self.summary_frame.pack_forget()
        
        Label(self.summary_frame, text="키워드:", font=self.heading_font, bg='#ffffff').pack(anchor=W, pady=5)
        self.keyword_label = Label(self.summary_frame, text="",
                                   font=self.normal_font, bg='#ffffff', fg='#555', justify=LEFT, anchor='w')
        self.keyword_label.pack(anchor=W, pady=5, fill=X)
        
        Label(self.summary_frame, text="요약:", font=self.heading_font, bg='#ffffff').pack(anchor=W, pady=5)
        self.summary_label = Label(self.summary_frame, 
                                   text="",
                                   font=self.normal_font, bg='#ffffff', fg='#555', justify=LEFT, anchor='w')
        self.summary_label.pack(anchor=W, pady=5, fill=X)
        
        ttk.Separator(self.summary_frame, orient=HORIZONTAL).pack(fill=X, pady=20)
        
        Label(self.summary_frame, text="📜 변환 및 원본 텍스트", font=self.heading_font, bg='#ffffff').pack(anchor=W, pady=5)
        self.conversion_text = scrolledtext.ScrolledText(self.summary_frame, height=15, width=80,
                                                         font=self.normal_font, wrap=WORD, bg='#ffffff')
        self.conversion_text.pack(fill=BOTH, expand=True, pady=5)
        self.conversion_text.config(state=DISABLED)

        # 요약/키워드 텍스트가 프레임 폭에 맞게 보이도록 wraplength 동적 조정
        def _update_wrap(event):
            w = event.width - 50  # 좌우 여백 보정 (padx 25 * 2)
            if w > 200:
                self.keyword_label.config(wraplength=w)
                self.summary_label.config(wraplength=w)
        self.summary_frame.bind("<Configure>", _update_wrap)
    
    def create_quiz_section(self):
        """퀴즈 섹션"""
        self.quiz_frame = LabelFrame(self.content_frame, text="❓ 예상 문제",
                                     font=self.heading_font, bg='#ffffff', padx=25, pady=25)
        self.quiz_frame.pack(fill=BOTH, expand=True, pady=10)
        self.quiz_frame.pack_forget()
        
        # 퀴즈 항목들
        self.quiz_canvas = Canvas(self.quiz_frame, bg='#ffffff', highlightthickness=0)
        quiz_scrollbar = Scrollbar(self.quiz_frame, orient="vertical", command=self.quiz_canvas.yview)
        self.quiz_content = Frame(self.quiz_canvas, bg='#ffffff')
        
        self.quiz_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        quiz_scrollbar.pack(side=RIGHT, fill=Y)
        self.quiz_canvas.configure(yscrollcommand=quiz_scrollbar.set)
        
        # Canvas의 너비에 맞춰 quiz_content가 확장되도록 설정
        self.quiz_window = self.quiz_canvas.create_window((0, 0), window=self.quiz_content, anchor="nw")
        
        def _update_quiz_canvas(event):
            # Canvas 너비에 맞춰 quiz_content 너비 조정
            canvas_width = event.width
            self.quiz_canvas.itemconfig(self.quiz_window, width=canvas_width)
            self.quiz_canvas.configure(scrollregion=self.quiz_canvas.bbox("all"))
        
        self.quiz_canvas.bind("<Configure>", _update_quiz_canvas)
        self.quiz_content.bind("<Configure>", lambda e: self.quiz_canvas.configure(scrollregion=self.quiz_canvas.bbox("all")))
        
        # 동적 퀴즈 위젯 리스트
        self.quiz_frames = []
        
        # 다음 문제 생성 버튼
        self.add_quiz_btn = Button(self.quiz_content, text="➕ 다음 문제 생성",
               bg='#2196F3', fg='white', font=self.heading_font, relief=FLAT, padx=30, pady=15)
        self.add_quiz_btn.pack(pady=10)
        
        # 채점 버튼 및 결과
        ttk.Separator(self.quiz_content, orient=HORIZONTAL).pack(fill=X, pady=20)
        
        self.final_score_label = Label(self.quiz_content, text="", font=self.heading_font,
                                       bg='#ffffff', fg='#333')
        self.final_score_label.pack(pady=10)
        self.final_score_label.pack_forget()
        
        self.score_btn = Button(self.quiz_content, text="✅ 정답 확인 및 채점",
               bg='#333333', fg='white', font=self.heading_font, relief=FLAT, padx=30, pady=15)
        self.score_btn.pack(pady=20)
    


