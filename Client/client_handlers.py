# client_handlers.py
# 클라이언트 이벤트 핸들러 모듈

import os
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tkinter import messagebox, filedialog, END, DISABLED, NORMAL
from tkinter import LabelFrame, Label, scrolledtext
from env_utils import DEFAULT_HOST, DEFAULT_PORT
from Client.client_core import TCPClient
from ai_services import OPENAI_AVAILABLE, OPENAI_ERROR, generate_keywords, generate_summary, generate_quiz, generate_single_quiz


class ClientHandlers:
    """클라이언트 이벤트 핸들러 클래스"""
    
    def __init__(self, ui, tcp_client):
        self.ui = ui
        self.tcp_client = tcp_client
        self.current_user_email = None
        self.current_file_id = None
        self.current_file_data = None
        self.current_quiz_data = None
        
        # 이벤트 바인딩
        self._bind_events()
    
    def _bind_events(self):
        """UI 이벤트 바인딩"""
        # 로그인 이벤트
        if hasattr(self.ui, 'login_btn'):
            self.ui.login_btn.config(command=self.handle_login)
        if hasattr(self.ui, 'logout_btn'):
            self.ui.logout_btn.config(command=self.handle_logout)
        
        # 서버 연결 버튼 제거 (자동 연결)
        self.ui.convert_btn.config(command=self.show_convert_form)
        self.ui.folder_btn.config(command=self.show_folder_form)
        self.ui.select_file_btn.config(command=self.select_audio_file)
        self.ui.convert_btn_main.config(command=self.handle_convert)
        self.ui.folder_tab_add.config(command=lambda: self.switch_folder_tab('add'))
        self.ui.folder_tab_update.config(command=lambda: self.switch_folder_tab('update'))
        self.ui.folder_tab_delete.config(command=lambda: self.switch_folder_tab('delete'))
        self.ui.folder_add_btn.config(command=self.handle_folder_add)
        self.ui.folder_update_btn.config(command=self.handle_folder_update)
        self.ui.folder_delete_btn.config(command=self.handle_folder_delete)
        self.ui.summary_btn.config(command=lambda: self.show_content('summary'))
        self.ui.quiz_btn.config(command=lambda: self.show_content('quiz'))
        self.ui.score_btn.config(command=self.score_quiz)
        self.ui.add_quiz_btn.config(command=self.add_quiz_question)
        self.ui.project_tree.tag_bind('file', '<Double-1>', self.on_file_select)
    
    def handle_login(self):
        """로그인 처리 (서버의 Folder 테이블에서 확인)"""
        username = self.ui.login_username_entry.get().strip()
        email = self.ui.login_email_entry.get().strip()
        password = self.ui.login_password_entry.get().strip()
        
        # 이메일은 필수
        if not email:
            self.ui.login_result_label.config(text="이메일을 입력해주세요.", fg='red')
            return
        
        # 사용자명이 없으면 이메일에서 추출
        if not username:
            username = email.split('@')[0]
        
        # 비밀번호가 없으면 빈 문자열로 처리 (선택사항)
        if not password:
            password = ""
        
        # 서버에 연결되어 있는지 확인
        if not self.tcp_client.is_connected:
            self.ui.login_result_label.config(text="먼저 서버에 연결해주세요.", fg='red')
            return
        
        # 서버에 로그인 요청 (Folder 테이블에서 확인)
        result = self.tcp_client.send_command("login", {
            "username": username,
            "email": email,
            "password": password
        })
        
        if result.get("status") == "success":
            user = result.get("user", {})
            self.current_user_email = email
            self.ui.current_user_email = email
            self.ui.current_username = user.get("user_name", username)
            self.ui.is_logged_in = True
            
            # 로그인 창 닫기
            self.ui.login_window.destroy()
            
            # 메인 창 표시
            self.ui.root.deiconify()
            
            # 로그인 상태 업데이트
            self.ui.login_status_label.config(text=f"로그인: {email}", fg='green')
            self.ui.logout_btn.pack(fill=X, pady=2)
            
            messagebox.showinfo("성공", result.get("message", "로그인 성공"))
        else:
            self.ui.login_result_label.config(
                text=result.get("message", "로그인 실패"), fg='red'
            )
    
    def handle_logout(self):
        """로그아웃 처리"""
        self.current_user_email = None
        self.ui.current_user_email = None
        self.ui.is_logged_in = False
        
        # 로그인 상태 업데이트
        self.ui.login_status_label.config(text="로그인 필요", fg='#f44336')
        self.ui.logout_btn.pack_forget()
        
        # 로그인 창 다시 표시
        self.ui.create_login_window()
        
        messagebox.showinfo("알림", "로그아웃되었습니다.")
    
    def connect_server(self):
        """서버 연결"""
        host = self.ui.server_host_entry.get().strip() or DEFAULT_HOST
        try:
            port = int(self.ui.server_port_entry.get().strip() or DEFAULT_PORT)
        except ValueError:
            messagebox.showerror("오류", "포트 번호는 숫자여야 합니다.")
            return
        
        if self.tcp_client.connect(host, port):
            self.ui.server_status_label.config(text=f"연결 상태: 연결됨 ({host}:{port})", fg='green')
            messagebox.showinfo("성공", "서버에 연결되었습니다.")
        else:
            self.ui.server_status_label.config(text="연결 상태: 연결 실패", fg='red')
            messagebox.showerror("오류", "서버에 연결할 수 없습니다.")
    
    def disconnect_server(self):
        """서버 연결 해제"""
        self.tcp_client.disconnect()
        self.ui.server_status_label.config(text="연결 상태: 미연결", fg='#666')
        messagebox.showinfo("알림", "서버 연결이 해제되었습니다.")
    
    def show_convert_form(self):
        """변환 폼 표시"""
        self.hide_all_forms()
        self.ui.convert_frame.pack(fill='x', pady=10)
        self.ui.document_header.pack_forget()
        self.ui.index_frame.pack_forget()
    
    def show_folder_form(self):
        """폴더 관리 폼 표시"""
        self.hide_all_forms()
        self.ui.folder_frame.pack(fill='x', pady=10)
        self.ui.document_header.pack_forget()
        self.ui.index_frame.pack_forget()
        self.switch_folder_tab('add')
    
    def switch_folder_tab(self, tab):
        """폴더 관리 탭 전환"""
        # 모든 탭 버튼 리셋
        self.ui.folder_tab_add.config(bg='#f0f0f0', fg='#666')
        self.ui.folder_tab_update.config(bg='#f0f0f0', fg='#666')
        self.ui.folder_tab_delete.config(bg='#f0f0f0', fg='#666')
        
        # 모든 섹션 숨기기
        self.ui.folder_add_section.pack_forget()
        self.ui.folder_update_section.pack_forget()
        self.ui.folder_delete_section.pack_forget()
        
        # 선택한 탭 활성화
        if tab == 'add':
            self.ui.folder_tab_add.config(bg='#333333', fg='white')
            self.ui.folder_add_section.pack(fill='x', pady=10)
        elif tab == 'update':
            self.ui.folder_tab_update.config(bg='#333333', fg='white')
            self.ui.folder_update_section.pack(fill='x', pady=10)
        elif tab == 'delete':
            self.ui.folder_tab_delete.config(bg='#333333', fg='white')
            self.ui.folder_delete_section.pack(fill='x', pady=10)
    
    def show_content(self, content_type):
        """콘텐츠 표시"""
        self.hide_all_forms()
        
        if content_type == 'summary':
            self.ui.summary_btn.config(bg='#333333', fg='white')
            self.ui.quiz_btn.config(bg='#f0f0f0', fg='#666')
            self.ui.summary_frame.pack(fill='both', expand=True, pady=10)
            self.ui.quiz_frame.pack_forget()
        elif content_type == 'quiz':
            self.ui.summary_btn.config(bg='#f0f0f0', fg='#666')
            self.ui.quiz_btn.config(bg='#333333', fg='white')
            self.ui.summary_frame.pack_forget()
            self.ui.quiz_frame.pack(fill='both', expand=True, pady=10)
            # 퀴즈 탭을 누르는 순간 OpenAI에 퀴즈 요청 (필요시)
            self.load_quiz_if_needed()
    
    def hide_all_forms(self):
        """모든 폼 숨기기"""
        self.ui.convert_frame.pack_forget()
        self.ui.folder_frame.pack_forget()
        self.ui.summary_frame.pack_forget()
        self.ui.quiz_frame.pack_forget()
    
    def load_file_list(self):
        """서버에서 파일 목록 로드하여 프로젝트 트리에 표시"""
        if not self.tcp_client.is_connected:
            return
        
        try:
            result = self.tcp_client.send_command("list_files", {})
            if result.get("status") == "success":
                files = result.get("files", [])
                # 기존 트리 항목 제거 (루트 제외)
                for item in self.ui.project_tree.get_children(self.ui.project_root):
                    self.ui.project_tree.delete(item)
                
                # 파일 목록 추가
                for file_data in files:
                    file_id = str(file_data.get('file_id'))
                    title = file_data.get('title', f'파일 {file_id}')
                    self.ui.project_tree.insert(
                        self.ui.project_root, 'end',
                        text=title,
                        tags=('file', file_id)
                    )
        except Exception as e:
            print(f"파일 목록 로드 오류: {e}")
    
    def on_file_select(self, event):
        """파일 선택 이벤트"""
        item = self.ui.project_tree.selection()[0]
        tags = self.ui.project_tree.item(item, 'tags')
        if 'file' in tags:
            file_id = tags[1] if len(tags) > 1 else None
            if file_id:
                self.load_file(file_id)
    
    def load_file(self, file_id):
        """파일 로드"""
        # 문서 헤더와 인덱스 버튼 표시
        self.ui.document_header.pack(fill='x', pady=(0, 20))
        self.ui.index_frame.pack(fill='x', pady=(0, 20))
        
        # 파일 제목 업데이트
        item = None
        for i in self.ui.project_tree.get_children():
            for j in self.ui.project_tree.get_children(i):
                for k in self.ui.project_tree.get_children(j):
                    if 'file' in self.ui.project_tree.item(k, 'tags'):
                        if self.ui.project_tree.item(k, 'tags')[1] == file_id:
                            item = k
                            break
        
        if item:
            title = self.ui.project_tree.item(item, 'text')
            self.ui.document_title.config(text=title)
        
        # 파일 변경 시 이전 퀴즈 데이터 초기화
        if self.current_file_id != int(file_id):
            self.current_quiz_data = None
            if hasattr(self.ui, 'quiz_frames'):
                self.build_quiz_ui({"questions": []})
        
        # 서버에서 파일 내용 로드
        if self.tcp_client.is_connected:
            result = self.tcp_client.send_command("load_file", {"file_id": int(file_id)})
            if result.get("status") == "success" and result.get("file_data"):
                self.current_file_id = int(file_id)
                self.current_file_data = result["file_data"]
                self.update_file_content(self.current_file_data)
                
                # 해당 파일의 퀴즈 데이터만 로드 (서버에서 file_id로 필터링됨)
                quiz_data = self.current_file_data.get("quiz")
                if quiz_data and quiz_data.get("questions"):
                    # quiz_id와 user_answer를 포함하도록 변환
                    quiz_data_with_ids = {
                        "questions": [
                            {
                                "question": q.get("question", ""),
                                "answer": q.get("answer", ""),
                                "explanation": q.get("explanation", ""),
                                "quiz_id": q.get("quiz_id"),
                                "user_answer": q.get("user_answer", "")  # 이전 답안 포함
                            }
                            for q in quiz_data.get("questions", [])
                        ]
                    }
                    self.current_quiz_data = quiz_data_with_ids
                    # 퀴즈 UI 업데이트 (퀴즈 탭이 보이지 않아도 데이터는 준비)
                    if hasattr(self.ui, 'quiz_frames'):
                        self.build_quiz_ui(quiz_data_with_ids)
                else:
                    # 해당 파일에 퀴즈가 없으면 빈 상태로 초기화
                    self.current_quiz_data = {"questions": []}
                    if hasattr(self.ui, 'quiz_frames'):
                        self.build_quiz_ui({"questions": []})
        
        # 기본적으로 요약 섹션 표시
        self.show_content('summary')
    
    def update_file_content(self, file_data):
        """파일 내용 업데이트"""
        if file_data.get("keywords"):
            self.ui.keyword_label.config(text=file_data["keywords"])
        if file_data.get("summary"):
            self.ui.summary_label.config(text=file_data["summary"])
        if file_data.get("text"):
            self.ui.conversion_text.config(state=NORMAL)
            self.ui.conversion_text.delete('1.0', END)
            self.ui.conversion_text.insert('1.0', file_data["text"])
            self.ui.conversion_text.config(state=DISABLED)
        # 퀴즈 데이터는 load_file에서 처리하므로 여기서는 업데이트하지 않음
    
    def select_audio_file(self):
        """오디오 파일 선택"""
        file_path = filedialog.askopenfilename(
            title="오디오 파일 선택",
            filetypes=[("오디오 파일", "*.mp3 *.wav *.m4a *.ogg *.flac"), ("모든 파일", "*.*")]
        )
        if file_path:
            self.selected_audio_file = file_path
            filename = os.path.basename(file_path)
            self.ui.audio_file_label.config(text=f"선택된 파일: {filename}")
    
    def handle_convert(self):
        """오디오 변환 처리 (클라이언트에서 OpenAI STT 직접 처리)"""
        if not hasattr(self, 'selected_audio_file') or not self.selected_audio_file:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return
        
        # 클라이언트에서 OpenAI STT 변환 처리
        try:
            from ai_services import STT_AVAILABLE, STT_ERROR, transcribe_audio
            
            if not STT_AVAILABLE:
                error_msg = "OpenAI API를 사용할 수 없습니다."
                if STT_ERROR:
                    error_msg += f"\n오류 상세: {STT_ERROR}"
                error_msg += "\n\n다음을 확인해주세요:"
                error_msg += "\n1. OpenAI API 키가 .env 파일에 설정되어 있는지 확인"
                error_msg += "\n2. openai 패키지가 설치되어 있는지 확인: pip install openai"
                messagebox.showerror("STT 오류", error_msg)
                return
            
            # 1단계: OpenAI STT 변환 (클라이언트에서 직접 처리)
            filename = os.path.basename(self.selected_audio_file)
            self.ui.convert_result_label.config(text="🔄 OpenAI STT 변환 중... (시간이 걸릴 수 있습니다)", fg='blue')
            self.ui.root.update()
            
            try:
                text = transcribe_audio(self.selected_audio_file, language="ko")
            except Exception as e:
                error_msg = f"STT 변환 실패: {str(e)}"
                self.ui.convert_result_label.config(text=f"❌ {error_msg}", fg='red')
                messagebox.showerror("STT 오류", error_msg)
                return

            if not text:
                messagebox.showwarning("경고", "변환된 텍스트가 없습니다.")
                return

            # 변환된 텍스트를 UI에 표시
            self.ui.conversion_text.config(state=NORMAL)
            self.ui.conversion_text.delete('1.0', END)
            self.ui.conversion_text.insert('1.0', text)
            self.ui.conversion_text.config(state=DISABLED)

            # 2단계: OpenAI로 요약/키워드 생성 (클라이언트에서 직접 호출)
            summary_text = ""
            keyword_text = ""
            if OPENAI_AVAILABLE:
                try:
                    self.ui.convert_result_label.config(text="🤖 OpenAI로 키워드/요약 생성 중...", fg='blue')
                    self.ui.root.update()

                    # 키워드
                    keyword_text = generate_keywords(text)

                    # 요약
                    summary_text = generate_summary(text)

                    # UI에 반영
                    if keyword_text:
                        self.ui.keyword_label.config(text=keyword_text)
                    if summary_text:
                        self.ui.summary_label.config(text=summary_text)

                except Exception as e:
                    # OpenAI 오류는 STT 결과 사용에는 영향 없게만 처리
                    self.ui.convert_result_label.config(
                        text=f"STT 완료, OpenAI 요약/키워드 생성 중 오류: {e}", fg='orange'
                    )

            # 3단계: 서버에 텍스트/요약/키워드 저장 요청 및 프로젝트 기록 반영
            if not self.tcp_client.is_connected:
                # 서버 연결 재시도
                from env_utils import DEFAULT_HOST, DEFAULT_PORT
                if not self.tcp_client.connect(DEFAULT_HOST, DEFAULT_PORT):
                    self.ui.convert_result_label.config(
                        text="✅ 변환 완료 (서버 연결 실패로 저장하지 않음)", 
                        fg='orange'
                    )
                    messagebox.showwarning("경고", "서버에 연결할 수 없어 데이터를 저장하지 못했습니다.")
                    return
            
            self.ui.convert_result_label.config(text="📤 DB에 저장 중...", fg='blue')
            self.ui.root.update()
            
            save_result = self.tcp_client.send_command("save_text", {
                "filename": filename,
                "text": text,
                "keywords": keyword_text,
                "summary": summary_text
            })
            
            if save_result.get("status") == "success":
                self.ui.convert_result_label.config(text="✅ 변환 완료 및 DB 저장 완료", fg='green')
                # 프로젝트 기록 트리 업데이트 (전체 목록 다시 로드)
                self.load_file_list()
                # 현재 파일 ID 저장
                file_id = str(save_result.get("file_id"))
                if file_id:
                    self.current_file_id = int(file_id)
            else:
                error_msg = save_result.get('message', '알 수 없는 오류')
                self.ui.convert_result_label.config(
                    text=f"✅ 변환 완료 (DB 저장 실패: {error_msg})",
                    fg='red'
                )
                messagebox.showerror("DB 저장 오류", f"데이터베이스 저장에 실패했습니다:\n{error_msg}")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.ui.convert_result_label.config(text=f"❌ STT/요약 처리 오류: {e}", fg='red')
            messagebox.showerror("오류", f"STT/요약 처리 중 오류가 발생했습니다:\n{e}")
    
    def handle_folder_add(self):
        """폴더 추가"""
        if not self.current_user_email:
            messagebox.showerror("오류", "사용자 이메일이 설정되지 않았습니다. 로그인이 필요합니다.")
            return
        
        folder_name = self.ui.folder_name_add_entry.get().strip()
        if not folder_name:
            messagebox.showwarning("경고", "폴더 이름을 입력해주세요.")
            return
        
        result = self.tcp_client.send_command("manage_folder", {
            "action": "create",
            "folder_name": folder_name,
            "user_email": self.current_user_email
        })
        
        if result.get("status") == "success":
            self.ui.folder_add_result.config(text=f"✅ {result.get('message', '폴더가 추가되었습니다.')}", fg='green')
        else:
            self.ui.folder_add_result.config(text=f"❌ {result.get('message', '폴더 추가 실패')}", fg='red')
    
    def handle_folder_update(self):
        """폴더 수정"""
        if not self.current_user_email:
            messagebox.showerror("오류", "사용자 이메일이 설정되지 않았습니다. 로그인이 필요합니다.")
            return
        
        old_name = self.ui.folder_name_old_entry.get().strip()
        new_name = self.ui.folder_name_new_entry.get().strip()
        
        if not old_name or not new_name:
            messagebox.showwarning("경고", "기존 폴더 이름과 새 폴더 이름을 모두 입력해주세요.")
            return
        
        result = self.tcp_client.send_command("manage_folder", {
            "action": "update",
            "folder_name": old_name,
            "user_email": self.current_user_email,
            "new_folder_name": new_name
        })
        
        if result.get("status") == "success":
            self.ui.folder_update_result.config(text=f"✅ {result.get('message', '폴더가 수정되었습니다.')}", fg='green')
        else:
            self.ui.folder_update_result.config(text=f"❌ {result.get('message', '폴더 수정 실패')}", fg='red')
    
    def handle_folder_delete(self):
        """폴더 삭제"""
        if not self.current_user_email:
            messagebox.showerror("오류", "사용자 이메일이 설정되지 않았습니다. 로그인이 필요합니다.")
            return
        
        folder_name = self.ui.folder_name_delete_entry.get().strip()
        if not folder_name:
            messagebox.showwarning("경고", "폴더 이름을 입력해주세요.")
            return
        
        if not messagebox.askyesno("확인", f'"{folder_name}" 폴더를 정말 삭제하시겠습니까?'):
            return
        
        result = self.tcp_client.send_command("manage_folder", {
            "action": "delete",
            "folder_name": folder_name,
            "user_email": self.current_user_email
        })
        
        if result.get("status") == "success":
            self.ui.folder_delete_result.config(text=f"✅ {result.get('message', '폴더가 삭제되었습니다.')}", fg='green')
        else:
            self.ui.folder_delete_result.config(text=f"❌ {result.get('message', '폴더 삭제 실패')}", fg='red')
    
    def score_quiz(self):
        """퀴즈 채점 및 답안 DB 저장"""
        if not getattr(self.ui, "quiz_frames", None):
            messagebox.showinfo("알림", "채점할 퀴즈가 없습니다.")
            return
        
        if not self.current_file_id:
            messagebox.showwarning("경고", "파일이 선택되지 않았습니다.")
            return
        
        correct_count = 0
        total_count = len(self.ui.quiz_frames)
        quiz_results = []  # DB 저장용
        
        for frame in self.ui.quiz_frames:
            user_answer = frame.input_box.get('1.0', END).strip()
            correct_answer = getattr(frame, "correct_answer", "").strip()
            explanation = getattr(frame, "explanation", "")
            quiz_id = getattr(frame, "quiz_id", None)
            
            # 간단한 포함 여부 기준 비교 (공백/대소문자 무시)
            ua_norm = user_answer.replace(" ", "").lower()
            ca_norm = correct_answer.replace(" ", "").lower()
            
            correct_is = False
            if ua_norm and ca_norm and ca_norm in ua_norm:
                frame.result_label.config(text="✅ 정답입니다!", fg='green')
                correct_count += 1
                correct_is = True
            else:
                msg = f"❌ 오답입니다.\n정답: {correct_answer}"
                if explanation:
                    msg += f"\n해설: {explanation}"
                frame.result_label.config(text=msg, fg='red')
            
            # DB 저장용 데이터 수집
            if quiz_id:
                quiz_results.append({
                    "quiz_id": quiz_id,
                    "user_answer": user_answer,
                    "correct_is": correct_is
                })
        
        if total_count > 0:
            percentage = int((correct_count / total_count) * 100)
            self.ui.final_score_label.config(
                text=f"🎯 최종 점수: {correct_count} / {total_count} 문제 ({percentage}점)"
            )
            self.ui.final_score_label.pack(pady=10)
        
        # 서버에 각 퀴즈의 답안 저장
        if self.tcp_client.is_connected and quiz_results:
            result = self.tcp_client.send_command("save_score", {
                "file_id": self.current_file_id,
                "quiz_results": quiz_results
            })
            if result.get("status") == "success":
                # 저장 성공 후 current_quiz_data 업데이트 (답안 반영)
                for i, q in enumerate(self.current_quiz_data.get("questions", [])):
                    for quiz_result in quiz_results:
                        if q.get("quiz_id") == quiz_result.get("quiz_id"):
                            self.current_quiz_data["questions"][i]["user_answer"] = quiz_result.get("user_answer", "")
                            break

    def load_quiz_if_needed(self):
        """현재 파일에 대해 DB에서 퀴즈 로드 (퀴즈 탭을 열 때 호출)"""
        if not self.current_file_id:
            return
        
        # 이미 로드된 퀴즈 데이터가 있고 현재 파일과 일치하면 그것을 사용
        if self.current_quiz_data and self.current_quiz_data.get("questions"):
            self.build_quiz_ui(self.current_quiz_data)
            return
        
        # 서버에서 현재 file_id에 해당하는 퀴즈만 로드 (다른 파일의 퀴즈가 표시되지 않도록)
        if self.tcp_client.is_connected:
            result = self.tcp_client.send_command("load_quizzes", {"file_id": self.current_file_id})
            if result.get("status") == "success":
                quizzes = result.get("quizzes", [])
                if quizzes:
                    # DB에서 로드한 퀴즈를 UI에 표시 (file_id로 필터링된 퀴즈만, 이전 답안 포함)
                    quiz_data = {
                        "questions": [
                            {
                                "question": q.get("question", ""),
                                "answer": q.get("correct_answer", ""),
                                "explanation": q.get("explanation", ""),
                                "quiz_id": q.get("quiz_id"),
                                "user_answer": q.get("user_answer", "")  # 이전 답안 포함
                            }
                            for q in quizzes
                        ]
                    }
                    self.current_quiz_data = quiz_data
                    self.build_quiz_ui(quiz_data)
                    return
        
        # 퀴즈가 없으면 빈 상태로 표시
        self.current_quiz_data = {"questions": []}
        self.build_quiz_ui({"questions": []})
    
    def add_quiz_question(self):
        """퀴즈 한 문제 추가 (OpenAI로 생성 후 DB에 저장)"""
        if not self.current_file_id or not self.current_file_data:
            messagebox.showwarning("경고", "파일을 먼저 선택해주세요.")
            return
        
        if not self.current_file_data.get("text"):
            messagebox.showwarning("경고", "퀴즈를 생성할 텍스트가 없습니다.")
            return
        
        if not OPENAI_AVAILABLE:
            messagebox.showerror(
                "오류",
                f"OpenAI API를 사용할 수 없습니다.\n\n{OPENAI_ERROR or 'OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.'}"
            )
            return
        
        if not self.tcp_client.is_connected:
            messagebox.showerror("오류", "서버에 연결되어 있지 않습니다.")
            return
        
        text = self.current_file_data["text"]
        
        # 기존 퀴즈 목록 가져오기 (중복 방지)
        existing_questions = []
        if hasattr(self.ui, 'quiz_frames') and self.ui.quiz_frames:
            for frame in self.ui.quiz_frames:
                if hasattr(frame, 'question_text'):
                    existing_questions.append({"question": frame.question_text})
        
        try:
            # 한 문제씩 생성
            self.ui.add_quiz_btn.config(state='disabled', text="생성 중...")
            self.ui.root.update()
            
            quiz_item = generate_single_quiz(text, existing_questions if existing_questions else None)
            
            # 서버로 전송하여 DB에 저장
            result = self.tcp_client.send_command("generate_single_quiz", {
                "file_id": self.current_file_id,
                "text": text,
                "question": quiz_item.get("question", ""),
                "answer": quiz_item.get("answer", ""),
                "explanation": quiz_item.get("explanation", "")
            })
            
            if result.get("status") == "success":
                quiz_id = result.get("quiz_id")
                # UI에 새 퀴즈 추가
                self.add_quiz_to_ui(quiz_item, quiz_id)
                
                # current_quiz_data 업데이트 (클라이언트 재시작 후에도 유지되도록)
                if not self.current_quiz_data:
                    self.current_quiz_data = {"questions": []}
                self.current_quiz_data["questions"].append({
                    "question": quiz_item.get("question", ""),
                    "answer": quiz_item.get("answer", ""),
                    "explanation": quiz_item.get("explanation", ""),
                    "quiz_id": quiz_id
                })
                
                messagebox.showinfo("성공", "퀴즈가 생성되어 DB에 저장되었습니다.")
            else:
                messagebox.showerror("오류", f"퀴즈 저장 실패: {result.get('message', '')}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("오류", f"퀴즈 생성 중 오류가 발생했습니다:\n{e}")
        finally:
            self.ui.add_quiz_btn.config(state='normal', text="➕ 다음 문제 생성")

    def build_quiz_ui(self, quiz_data):
        """DB에서 받은 퀴즈 데이터를 기준으로 UI 구성"""
        # 기존 퀴즈 위젯 제거 (버튼과 구분선은 유지)
        for child in self.ui.quiz_content.winfo_children():
            if isinstance(child, LabelFrame):
                child.destroy()
        self.ui.quiz_frames.clear()
        self.ui.final_score_label.config(text="")
        self.ui.final_score_label.pack_forget()
        
        questions = quiz_data.get("questions", [])
        for idx, q in enumerate(questions, start=1):
            quiz_id = q.get("quiz_id")
            self.add_quiz_to_ui(q, quiz_id, idx)
    
    def add_quiz_to_ui(self, quiz_item, quiz_id=None, index=None):
        """퀴즈 한 문제를 UI에 추가 (이전 답안 포함)"""
        if index is None:
            index = len(self.ui.quiz_frames) + 1
        
        frame = LabelFrame(self.ui.quiz_content, text=f"문제 {index}",
                           font=self.ui.heading_font, bg='#ffffff', padx=20, pady=15)
        # add_quiz_btn 앞에 삽입
        frame.pack(fill='both', expand=True, pady=10, before=self.ui.add_quiz_btn)
        
        # 문제 텍스트 라벨
        question_text = quiz_item.get("question", "")
        question_label = Label(frame, text=question_text, font=self.ui.normal_font,
                              bg='#ffffff', justify='left')
        question_label.pack(anchor='w', pady=5, fill='x')
        
        # 문제 텍스트가 프레임 폭에 맞게 보이도록 wraplength 동적 조정
        def _update_question_wrap(event, label=question_label):
            w = event.width - 50
            if w > 200:
                label.config(wraplength=w)
        frame.bind("<Configure>", _update_question_wrap)
        
        # 답안 입력창 (이전 답안이 있으면 표시)
        input_box = scrolledtext.ScrolledText(frame, height=8,
                                              font=self.ui.normal_font, wrap='word')
        input_box.pack(fill='both', expand=True, pady=10, padx=5)
        
        # 이전 답안이 있으면 입력창에 표시
        user_answer = quiz_item.get("user_answer", "")
        if user_answer:
            input_box.insert('1.0', user_answer)
        
        result_label = Label(frame, text="", font=self.ui.normal_font, bg='#ffffff')
        result_label.pack(anchor='w', pady=5)
        
        # 정답/해설/퀴즈ID 저장
        frame.input_box = input_box
        frame.result_label = result_label
        frame.correct_answer = quiz_item.get("answer", "")
        frame.explanation = quiz_item.get("explanation", "")
        frame.quiz_id = quiz_id
        frame.question_text = question_text
        
        self.ui.quiz_frames.append(frame)

