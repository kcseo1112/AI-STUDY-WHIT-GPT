# server_handlers.py
# 서버 명령 처리 핸들러

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env_utils import RECEIVE_DIR
from ai_services import OPENAI_AVAILABLE, openai_client, analyze_text, generate_quiz


class ServerCommandHandlers:
    """서버 명령 처리 핸들러 클래스"""
    
    def __init__(self, data_manager, log_callback=None):
        self.data_manager = data_manager
        self._log = log_callback or (lambda msg: print(msg))
    
    def handle_login(self, data):
        """로그인 처리 (Folder 테이블 기반)"""
        username = data.get("username", "")
        email = data.get("email")
        password = data.get("password", "")
        
        if not email:
            return {"status": "error", "message": "이메일을 입력해주세요."}
        
        # 사용자명이 없으면 이메일에서 추출
        if not username:
            username = email.split('@')[0]
        
        # 비밀번호가 없으면 빈 문자열로 처리 (선택사항)
        if not password:
            password = ""
        
        # Folder 테이블에서 이메일과 비밀번호로 사용자 확인
        user = self.data_manager.get_user_by_email_password(email, password)
        
        if user:
            # 로그인 성공
            return {
                "status": "success",
                "message": "로그인 성공",
                "user": {
                    "folder_id": user.get("folder_id"),
                    "user_name": user.get("user_name"),
                    "email": user.get("email")
                }
            }
        else:
            # 새 사용자 등록 - 기본 폴더와 함께 생성
            new_folder = self.data_manager.create_user_with_default_folder(
                username=username,
                email=email,
                password=password,
                default_folder_title="메인파일"
            )
            if new_folder:
                return {
                    "status": "success",
                    "message": "새 사용자로 등록되었습니다. 기본 폴더가 생성되었습니다.",
                    "user": {
                        "folder_id": new_folder.get("folder_id"),
                        "user_name": new_folder.get("user_name"),
                        "email": new_folder.get("email")
                    }
                }
            else:
                return {"status": "error", "message": "사용자 등록에 실패했습니다."}
    
    def handle_save_text(self, data):
        """클라이언트에서 변환된 텍스트를 서버에 저장 (File 테이블만 사용)"""
        filename = data.get("filename")
        text = data.get("text", "")
        keywords = data.get("keywords", "")
        summary = data.get("summary", "")
        
        if not filename:
            return {"status": "error", "message": "파일명이 제공되지 않았습니다."}
        
        if not text:
            return {"status": "error", "message": "텍스트가 비어있습니다."}
        
        try:
            base_name, _ = os.path.splitext(filename)
            
            # 1) 원본 텍스트 파일 저장
            text_file = os.path.join(RECEIVE_DIR, f"{base_name}.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self._log(f"텍스트 저장 완료: {text_file}")
            
            # 2) 요약 파일 경로 생성 (클라이언트에서 전송한 키워드/요약 사용)
            summary_file_path = None
            if keywords or summary:
                summary_filename = f"{base_name}_sub.txt"
                summary_file_path = os.path.join(RECEIVE_DIR, summary_filename)
                with open(summary_file_path, 'w', encoding='utf-8') as f:
                    if keywords:
                        f.write("[키워드]\n")
                        f.write(keywords + "\n\n")
                    if summary:
                        f.write("[요약]\n")
                        f.write(summary)
            
            # File 테이블에 파일 등록 (folder_id는 NULL로 설정 - 단일 사용자 프로젝트)
            # keywords와 summary는 summary_file_path 파일에만 저장 (테이블 컬럼 사용 안 함)
            file_data = self.data_manager.create_file(
                folder_id=None,  # 단일 사용자 프로젝트이므로 folder_id 불필요
                title=base_name,
                file_path=text_file,
                convert_file_path=text_file,
                summary_file_path=summary_file_path
            )
            
            if not file_data:
                return {"status": "error", "message": "파일 저장 실패"}
            
            file_id = file_data.get('file_id')
            
            return {
                "status": "success",
                "message": "텍스트 및 서브 파일 저장 완료",
                "file_id": file_id,
                "text_file": text_file
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": f"텍스트 저장 오류: {e}"}
    
    def handle_manage_folder(self, data):
        """폴더 관리 (ERD 구조: Folder 테이블)"""
        action = data.get("action")
        folder_name = data.get("folder_name")
        user_email = data.get("user_email")
        new_folder_name = data.get("new_folder_name")
        
        # 사용자 정보 가져오기
        user_folders = self.data_manager.get_user_folders(user_email)
        if not user_folders:
            return {"status": "error", "message": "사용자를 찾을 수 없습니다."}
        
        first_folder = user_folders[0]
        user_name = first_folder.get('user_name', '')
        password = first_folder.get('password', '')
        
        if action == "create":
            # 새 폴더 생성 (부모 폴더는 NULL 또는 기본 폴더)
            new_folder = self.data_manager.create_folder(
                p_folder_id=None,  # 최상위 폴더
                title=folder_name,
                user_name=user_name,
                email=user_email,
                password=password
            )
            if new_folder:
                return {"status": "success", "message": f"폴더 '{folder_name}'가 생성되었습니다."}
            else:
                return {"status": "error", "message": "폴더 생성에 실패했습니다."}
        
        elif action == "update":
            # 폴더 이름 변경
            folders = self.data_manager.get_user_folders(user_email)
            target_folder = None
            for folder in folders:
                if folder.get('title') == folder_name:
                    target_folder = folder
                    break
            
            if not target_folder:
                return {"status": "error", "message": "폴더를 찾을 수 없습니다."}
            
            updated = self.data_manager.update_folder(
                target_folder.get('folder_id'),
                title=new_folder_name
            )
            if updated:
                return {"status": "success", "message": f"폴더가 '{new_folder_name}'로 변경되었습니다."}
            else:
                return {"status": "error", "message": "폴더 수정에 실패했습니다."}
        
        elif action == "delete":
            # 폴더 삭제
            folders = self.data_manager.get_user_folders(user_email)
            target_folder = None
            for folder in folders:
                if folder.get('title') == folder_name:
                    target_folder = folder
                    break
            
            if not target_folder:
                return {"status": "error", "message": "폴더를 찾을 수 없습니다."}
            
            # 기본 폴더는 삭제 불가
            if target_folder.get('title') == '메인파일' and len(folders) == 1:
                return {"status": "error", "message": "기본 폴더는 삭제할 수 없습니다."}
            
            success = self.data_manager.delete_folder(target_folder.get('folder_id'))
            if success:
                return {"status": "success", "message": f"폴더 '{folder_name}'가 삭제되었습니다."}
            else:
                return {"status": "error", "message": "폴더 삭제에 실패했습니다."}
        
        else:
            return {"status": "error", "message": "알 수 없는 작업입니다."}
    
    def handle_load_file(self, data):
        """파일 내용 로드 (ERD 구조: File 테이블)"""
        file_id = data.get("file_id")
        
        file_data = self.data_manager.get_file(file_id)
        if file_data:
            # 파일 경로에서 텍스트 읽기
            file_path = file_data.get('file_path') or file_data.get('convert_file_path')
            text = ""
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                except Exception as e:
                    self._log(f"파일 읽기 오류: {e}")
            
            # 요약 파일 경로에서 키워드/요약 읽기 (summary_file_path 파일에서 읽기)
            keyword_text = ""
            summary_text = ""
            summary_file_path = file_data.get('summary_file_path')
            if summary_file_path and os.path.exists(summary_file_path):
                try:
                    with open(summary_file_path, 'r', encoding='utf-8') as f:
                        summary_content = f.read()
                        # 키워드와 요약 추출
                        if "[키워드]" in summary_content:
                            parts = summary_content.split("[요약]")
                            keyword_text = parts[0].replace("[키워드]", "").strip()
                            if len(parts) > 1:
                                summary_text = parts[1].strip()
                        elif "[요약]" in summary_content:
                            summary_text = summary_content.replace("[요약]", "").strip()
                except Exception as e:
                    self._log(f"요약 파일 읽기 오류: {e}")
            
            # 퀴즈 데이터 가져오기 (이전 답안 포함)
            quizzes = self.data_manager.get_quizzes_by_file(file_id)
            quiz_data = None
            if quizzes:
                quiz_data = {
                    "questions": []
                }
                for quiz in quizzes:
                    quiz_data["questions"].append({
                        "question": quiz.get('question', ''),
                        "answer": quiz.get('correct_answer', ''),
                        "explanation": quiz.get('explanation', ''),
                        "quiz_id": quiz.get('quiz_id'),
                        "user_answer": quiz.get('user_answer', '')  # 이전 답안 포함
                    })
            
            return {
                "status": "success",
                "file_data": {
                    "file_id": file_data.get('file_id'),
                    "title": file_data.get('title'),
                    "text": text,
                    "keywords": keyword_text,
                    "summary": summary_text,
                    "quiz": quiz_data
                }
            }
        else:
            return {"status": "error", "message": "파일을 찾을 수 없습니다."}
    
    def handle_save_score(self, data):
        """채점 결과 저장 (ERD 구조: Quiz 테이블의 correct_is 업데이트)"""
        file_id = data.get("file_id")
        quiz_results = data.get("quiz_results", [])  # [{"quiz_id": 1, "user_answer": "...", "correct_is": True}, ...]
        
        if not file_id:
            # 기존 방식 호환성 (quiz_results가 없으면 단순 점수만 저장)
            correct = data.get("correct", 0)
            total = data.get("total", 0)
            self._log(f"점수 저장: {correct}/{total}")
            return {"status": "success", "message": "점수가 저장되었습니다."}
        
        try:
            updated_count = 0
            for result in quiz_results:
                quiz_id = result.get("quiz_id")
                user_answer = result.get("user_answer", "")
                correct_is = result.get("correct_is", False)
                
                if quiz_id:
                    updated = self.data_manager.update_quiz(
                        quiz_id=quiz_id,
                        user_answer=user_answer,
                        correct_is=correct_is
                    )
                    if updated:
                        updated_count += 1
            
            return {
                "status": "success",
                "message": f"{updated_count}개의 퀴즈 답안이 저장되었습니다."
            }
        except Exception as e:
            return {"status": "error", "message": f"점수 저장 오류: {e}"}
    
    def handle_generate_quiz(self, data):
        """퀴즈 생성 (ERD 구조: Quiz 테이블에 저장) - 여러 문제"""
        file_id = data.get("file_id")
        text = data.get("text")
        count = data.get("count", 5)
        
        if not file_id:
            return {"status": "error", "message": "파일 ID가 제공되지 않았습니다."}
        
        if not text:
            return {"status": "error", "message": "텍스트가 제공되지 않았습니다."}
        
        try:
            # OpenAI로 퀴즈 생성
            quiz_data = generate_quiz(text, count)
            
            # Quiz 테이블에 저장
            saved_quizzes = []
            for question_data in quiz_data.get("questions", []):
                quiz = self.data_manager.create_quiz(
                    file_id=file_id,
                    question=question_data.get("question", ""),
                    example=None,  # OpenAI 응답에 example이 없으면 None
                    correct_answer=question_data.get("answer", ""),
                    explanation=question_data.get("explanation", ""),
                    user_answer=None,
                    correct_is=False
                )
                if quiz:
                    saved_quizzes.append(quiz)
            
            return {
                "status": "success",
                "quiz": quiz_data,
                "message": f"{len(saved_quizzes)}개의 퀴즈가 저장되었습니다."
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": f"퀴즈 생성 오류: {e}"}
    
    def handle_generate_single_quiz(self, data):
        """퀴즈 한 문제 생성 및 DB 저장"""
        file_id = data.get("file_id")
        question = data.get("question")
        answer = data.get("answer")
        explanation = data.get("explanation")
        
        if not file_id:
            return {"status": "error", "message": "파일 ID가 제공되지 않았습니다."}
        
        if not question or not answer:
            return {"status": "error", "message": "문제와 정답이 제공되지 않았습니다."}
        
        try:
            # Quiz 테이블에 저장
            quiz = self.data_manager.create_quiz(
                file_id=file_id,
                question=question,
                example=None,
                correct_answer=answer,
                explanation=explanation,
                user_answer=None,
                correct_is=False
            )
            
            if quiz:
                return {
                    "status": "success",
                    "quiz_id": quiz.get('quiz_id'),
                    "message": "퀴즈가 저장되었습니다."
                }
            else:
                return {"status": "error", "message": "퀴즈 저장 실패"}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": f"퀴즈 저장 오류: {e}"}
    
    def handle_load_quizzes(self, data):
        """파일에 속한 퀴즈 목록 로드"""
        file_id = data.get("file_id")
        
        if not file_id:
            return {"status": "error", "message": "파일 ID가 제공되지 않았습니다."}
        
        try:
            quizzes = self.data_manager.get_quizzes_by_file(file_id)
            return {
                "status": "success",
                "quizzes": quizzes
            }
        except Exception as e:
            return {"status": "error", "message": f"퀴즈 로드 오류: {e}"}
    
    def handle_list_files(self, data):
        """모든 파일 목록 조회"""
        try:
            files = self.data_manager.get_all_files()
            return {
                "status": "success",
                "files": files
            }
        except Exception as e:
            return {"status": "error", "message": f"파일 목록 조회 오류: {e}"}
    
    def handle_analyze_text(self, data):
        """텍스트 분석 (키워드/요약)"""
        analysis_type = data.get("type")
        text = data.get("text")
        
        try:
            result = analyze_text(text, analysis_type)
            return {
                "status": "success",
                "type": analysis_type,
                "result": result
            }
        except Exception as e:
            return {"status": "error", "message": f"분석 오류: {e}"}
    
    def handle_convert_audio(self, data):
        """오디오 파일 변환 (STT) - 서버에서 처리 (OpenAI Whisper API 사용)"""
        from ai_services import STT_AVAILABLE, STT_ERROR, transcribe_audio
        
        filename = data.get("filename")
        file_path = os.path.join(RECEIVE_DIR, filename)
        
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"파일을 찾을 수 없습니다: {filename}"}
        
        if not STT_AVAILABLE:
            error_msg = "OpenAI API를 사용할 수 없습니다."
            if STT_ERROR:
                error_msg += f"\n오류 상세: {STT_ERROR}"
            error_msg += "\n\n서버에 다음을 확인해주세요:"
            error_msg += "\n1. OpenAI API 키가 .env 파일에 설정되어 있는지 확인"
            error_msg += "\n2. openai 패키지가 설치되어 있는지 확인: pip install openai"
            return {"status": "error", "message": error_msg}
        
        try:
            # OpenAI Whisper API를 사용한 변환
            self._log(f"오디오 변환 시작: {filename} (OpenAI Whisper API 사용)")
            text = transcribe_audio(file_path)
            
            # 변환된 텍스트를 파일로 저장
            text_file = os.path.join(RECEIVE_DIR, f"{os.path.splitext(filename)[0]}.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self._log(f"오디오 변환 완료: {filename} -> {len(text)}자")
            
            return {
                "status": "success",
                "message": "변환 완료",
                "text": text,
                "text_file": text_file
            }
        except Exception as e:
            error_msg = f"변환 오류: {e}"
            self._log(f"오디오 변환 오류 ({filename}): {e}")
            return {"status": "error", "message": error_msg}


