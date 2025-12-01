# server_data_supabase.py
# 서버 데이터 관리 모듈 (Supabase 연동 - ERD 구조)

import os
import sys
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import supabase, SUPABASE_AVAILABLE


class ServerDataManager:
    """서버 데이터 관리 클래스 (Supabase 사용 - ERD 구조)"""
    
    def __init__(self):
        self.supabase = supabase
        self.use_supabase = SUPABASE_AVAILABLE
        
        if not self.use_supabase:
            print("경고: Supabase를 사용할 수 없습니다. JSON 파일 모드로 폴백합니다.")
            self._init_json_fallback()
        else:
            print("Supabase 데이터베이스 모드로 초기화되었습니다. (ERD 구조)")
    
    def _init_json_fallback(self):
        """JSON 파일 폴백 모드 초기화"""
        from env_utils import DATA_DIR
        self.folders_file = os.path.join(DATA_DIR, "folders.json")
        self.files_file = os.path.join(DATA_DIR, "files.json")
        self.quizzes_file = os.path.join(DATA_DIR, "quizzes.json")
        os.makedirs(DATA_DIR, exist_ok=True)
        self.load_data()
    
    def load_data(self):
        """데이터 로드 (JSON 폴백용)"""
        if self.use_supabase:
            return  # Supabase는 실시간으로 데이터를 가져오므로 로드 불필요
        
        # JSON 폴백 모드
        if os.path.exists(self.folders_file):
            with open(self.folders_file, 'r', encoding='utf-8') as f:
                self._folders = json.load(f)
        else:
            self._folders = {}
        
        if os.path.exists(self.files_file):
            with open(self.files_file, 'r', encoding='utf-8') as f:
                self._files = json.load(f)
        else:
            self._files = {}
        
        if os.path.exists(self.quizzes_file):
            with open(self.quizzes_file, 'r', encoding='utf-8') as f:
                self._quizzes = json.load(f)
        else:
            self._quizzes = {}
    
    def save_data(self):
        """데이터 저장 (JSON 폴백용)"""
        if self.use_supabase:
            return  # Supabase는 각 작업마다 저장되므로 일괄 저장 불필요
        
        # JSON 폴백 모드
        with open(self.folders_file, 'w', encoding='utf-8') as f:
            json.dump(self._folders, f, ensure_ascii=False, indent=2)
        with open(self.files_file, 'w', encoding='utf-8') as f:
            json.dump(self._files, f, ensure_ascii=False, indent=2)
        with open(self.quizzes_file, 'w', encoding='utf-8') as f:
            json.dump(self._quizzes, f, ensure_ascii=False, indent=2)
    
    # === 로그인 관련 메서드 (Folder 테이블 사용) ===
    
    def get_user_by_email_password(self, email, password):
        """이메일과 비밀번호로 사용자 조회 (Folder 테이블)"""
        if self.use_supabase:
            try:
                result = self.supabase.table('Folder').select('*').eq('email', email).eq('password', password).execute()
                if result.data and len(result.data) > 0:
                    return result.data[0]  # 첫 번째 매칭되는 폴더 반환
                return None
            except Exception as e:
                print(f"사용자 조회 오류: {e}")
                return None
        else:
            # JSON 폴백 모드
            for folder_id, folder_data in self._folders.items():
                if folder_data.get('email') == email and folder_data.get('password') == password:
                    return folder_data
            return None
    
    def get_user_folders(self, email):
        """사용자의 모든 폴더 조회"""
        if self.use_supabase:
            try:
                result = self.supabase.table('Folder').select('*').eq('email', email).execute()
                return result.data if result.data else []
            except Exception as e:
                print(f"폴더 조회 오류: {e}")
                return []
        else:
            folders = []
            for folder_id, folder_data in self._folders.items():
                if folder_data.get('email') == email:
                    folders.append(folder_data)
            return folders
    
    def create_user_with_default_folder(self, username, email, password, default_folder_title="메인파일"):
        """새 사용자 생성 및 기본 폴더 생성 (Folder 테이블)"""
        if self.use_supabase:
            try:
                # 기본 폴더 생성 (p_folder_id는 NULL)
                result = self.supabase.table('Folder').insert({
                    'p_folder_id': None,
                    'title': default_folder_title,
                    'user_name': username,
                    'email': email,
                    'password': password
                }).execute()
                if result.data:
                    return result.data[0]
                return None
            except Exception as e:
                print(f"사용자 생성 오류: {e}")
                import traceback
                traceback.print_exc()
                return None
        else:
            # JSON 폴백 모드
            folder_id = str(len(self._folders) + 1)
            folder_data = {
                'folder_id': folder_id,
                'p_folder_id': None,
                'title': default_folder_title,
                'user_name': username,
                'email': email,
                'password': password,
                'created_at': datetime.now().isoformat()
            }
            self._folders[folder_id] = folder_data
            self.save_data()
            return folder_data
    
    # === Folder 관련 메서드 ===
    
    def get_folder(self, folder_id):
        """폴더 조회"""
        if self.use_supabase:
            try:
                result = self.supabase.table('Folder').select('*').eq('folder_id', folder_id).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                print(f"폴더 조회 오류: {e}")
                return None
        else:
            return self._folders.get(str(folder_id))
    
    def create_folder(self, p_folder_id, title, user_name, email, password):
        """폴더 생성"""
        if self.use_supabase:
            try:
                result = self.supabase.table('Folder').insert({
                    'p_folder_id': p_folder_id,
                    'title': title,
                    'user_name': user_name,
                    'email': email,
                    'password': password
                }).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                print(f"폴더 생성 오류: {e}")
                return None
        else:
            folder_id = str(len(self._folders) + 1)
            folder_data = {
                'folder_id': folder_id,
                'p_folder_id': p_folder_id,
                'title': title,
                'user_name': user_name,
                'email': email,
                'password': password,
                'created_at': datetime.now().isoformat()
            }
            self._folders[folder_id] = folder_data
            self.save_data()
            return folder_data
    
    def update_folder(self, folder_id, **kwargs):
        """폴더 업데이트"""
        if self.use_supabase:
            try:
                result = self.supabase.table('Folder').update(kwargs).eq('folder_id', folder_id).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                print(f"폴더 업데이트 오류: {e}")
                return None
        else:
            folder_id_str = str(folder_id)
            if folder_id_str in self._folders:
                self._folders[folder_id_str].update(kwargs)
                self.save_data()
                return self._folders[folder_id_str]
            return None
    
    def delete_folder(self, folder_id):
        """폴더 삭제"""
        if self.use_supabase:
            try:
                result = self.supabase.table('Folder').delete().eq('folder_id', folder_id).execute()
                return True
            except Exception as e:
                print(f"폴더 삭제 오류: {e}")
                return False
        else:
            folder_id_str = str(folder_id)
            if folder_id_str in self._folders:
                del self._folders[folder_id_str]
                self.save_data()
                return True
            return False
    
    # === File 관련 메서드 ===
    
    def get_file(self, file_id):
        """파일 조회"""
        if self.use_supabase:
            try:
                result = self.supabase.table('File').select('*').eq('file_id', file_id).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                print(f"파일 조회 오류: {e}")
                return None
        else:
            return self._files.get(str(file_id))
    
    def get_files_by_folder(self, folder_id=None):
        """파일 목록 조회 (단일 사용자 프로젝트 - folder_id는 선택사항)"""
        if self.use_supabase:
            try:
                if folder_id is None:
                    # folder_id가 None이면 모든 파일 조회
                    result = self.supabase.table('File').select('*').order('created_at', desc=True).execute()
                else:
                    result = self.supabase.table('File').select('*').eq('folder_id', folder_id).order('created_at', desc=True).execute()
                return result.data if result.data else []
            except Exception as e:
                print(f"파일 목록 조회 오류: {e}")
                return []
        else:
            files = []
            for file_id, file_data in self._files.items():
                if folder_id is None or file_data.get('folder_id') == folder_id:
                    files.append(file_data)
            return files
    
    def get_all_files(self):
        """모든 파일 조회 (단일 사용자 프로젝트)"""
        return self.get_files_by_folder(folder_id=None)
    
    def create_file(self, folder_id=None, title=None, file_path=None, convert_file_path=None, summary_file_path=None):
        """파일 생성 (단일 사용자 프로젝트 - folder_id는 선택사항)"""
        if self.use_supabase:
            try:
                file_data = {
                    'title': title
                }
                if folder_id is not None:
                    file_data['folder_id'] = folder_id
                if file_path:
                    file_data['file_path'] = file_path
                if convert_file_path:
                    file_data['convert_file_path'] = convert_file_path
                if summary_file_path:
                    file_data['summary_file_path'] = summary_file_path
                
                result = self.supabase.table('File').insert(file_data).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                print(f"파일 생성 오류: {e}")
                import traceback
                traceback.print_exc()
                return None
        else:
            file_id = str(len(self._files) + 1)
            file_data = {
                'file_id': file_id,
                'folder_id': folder_id,
                'title': title,
                'file_path': file_path,
                'convert_file_path': convert_file_path,
                'summary_file_path': summary_file_path,
                'created_at': datetime.now().isoformat()
            }
            self._files[file_id] = file_data
            self.save_data()
            return file_data
    
    def update_file(self, file_id, **kwargs):
        """파일 업데이트"""
        if self.use_supabase:
            try:
                result = self.supabase.table('File').update(kwargs).eq('file_id', file_id).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                print(f"파일 업데이트 오류: {e}")
                return None
        else:
            file_id_str = str(file_id)
            if file_id_str in self._files:
                self._files[file_id_str].update(kwargs)
                self.save_data()
                return self._files[file_id_str]
            return None
    
    def delete_file(self, file_id):
        """파일 삭제"""
        if self.use_supabase:
            try:
                result = self.supabase.table('File').delete().eq('file_id', file_id).execute()
                return True
            except Exception as e:
                print(f"파일 삭제 오류: {e}")
                return False
        else:
            file_id_str = str(file_id)
            if file_id_str in self._files:
                del self._files[file_id_str]
                self.save_data()
                return True
            return False
    
    # === Quiz 관련 메서드 ===
    
    def get_quiz(self, quiz_id):
        """퀴즈 조회"""
        if self.use_supabase:
            try:
                result = self.supabase.table('Quiz').select('*').eq('quiz_id', quiz_id).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                print(f"퀴즈 조회 오류: {e}")
                return None
        else:
            return self._quizzes.get(str(quiz_id))
    
    def get_quizzes_by_file(self, file_id):
        """파일에 속한 퀴즈 목록 조회"""
        if self.use_supabase:
            try:
                result = self.supabase.table('Quiz').select('*').eq('file_id', file_id).execute()
                return result.data if result.data else []
            except Exception as e:
                print(f"퀴즈 목록 조회 오류: {e}")
                return []
        else:
            quizzes = []
            for quiz_id, quiz_data in self._quizzes.items():
                if quiz_data.get('file_id') == file_id:
                    quizzes.append(quiz_data)
            return quizzes
    
    def create_quiz(self, file_id, question, example=None, correct_answer=None, explanation=None, user_answer=None, correct_is=False):
        """퀴즈 생성"""
        if self.use_supabase:
            try:
                quiz_data = {
                    'file_id': file_id,
                    'question': question,
                    'correct_is': correct_is
                }
                if example:
                    quiz_data['example'] = example
                if correct_answer:
                    quiz_data['correct_answer'] = correct_answer
                if explanation:
                    quiz_data['explanation'] = explanation
                if user_answer:
                    quiz_data['user_answer'] = user_answer
                
                result = self.supabase.table('Quiz').insert(quiz_data).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                print(f"퀴즈 생성 오류: {e}")
                import traceback
                traceback.print_exc()
                return None
        else:
            quiz_id = str(len(self._quizzes) + 1)
            quiz_data = {
                'quiz_id': quiz_id,
                'file_id': file_id,
                'question': question,
                'example': example,
                'correct_answer': correct_answer,
                'explanation': explanation,
                'user_answer': user_answer,
                'correct_is': correct_is,
                'created_at': datetime.now().isoformat()
            }
            self._quizzes[quiz_id] = quiz_data
            self.save_data()
            return quiz_data
    
    def update_quiz(self, quiz_id, **kwargs):
        """퀴즈 업데이트"""
        if self.use_supabase:
            try:
                result = self.supabase.table('Quiz').update(kwargs).eq('quiz_id', quiz_id).execute()
                return result.data[0] if result.data else None
            except Exception as e:
                print(f"퀴즈 업데이트 오류: {e}")
                return None
        else:
            quiz_id_str = str(quiz_id)
            if quiz_id_str in self._quizzes:
                self._quizzes[quiz_id_str].update(kwargs)
                self.save_data()
                return self._quizzes[quiz_id_str]
            return None
    
    def delete_quiz(self, quiz_id):
        """퀴즈 삭제"""
        if self.use_supabase:
            try:
                result = self.supabase.table('Quiz').delete().eq('quiz_id', quiz_id).execute()
                return True
            except Exception as e:
                print(f"퀴즈 삭제 오류: {e}")
                return False
        else:
            quiz_id_str = str(quiz_id)
            if quiz_id_str in self._quizzes:
                del self._quizzes[quiz_id_str]
                self.save_data()
                return True
            return False
    
    # === 호환성을 위한 메서드 (기존 코드와의 호환) ===
    
    def get_user(self, email):
        """사용자 조회 (호환성 - Folder 테이블에서 첫 번째 폴더 반환)"""
        folders = self.get_user_folders(email)
        return folders[0] if folders else None
    
    def create_user(self, username, email, password):
        """사용자 생성 (호환성 - 기본 폴더와 함께 생성)"""
        return self.create_user_with_default_folder(username, email, password)
    
    def get_folders(self, user_email):
        """사용자의 폴더 목록 조회 (호환성)"""
        folders = self.get_user_folders(user_email)
        return [f['title'] for f in folders] if folders else []
    
    def create_folder(self, user_email, folder_name):
        """폴더 생성 (호환성 - 기존 사용자 정보 필요)"""
        # 기존 사용자의 폴더를 찾아서 user_name과 password 가져오기
        user_folders = self.get_user_folders(user_email)
        if not user_folders:
            return False
        
        first_folder = user_folders[0]
        return self.create_folder(
            p_folder_id=None,
            title=folder_name,
            user_name=first_folder.get('user_name', ''),
            email=user_email,
            password=first_folder.get('password', '')
        ) is not None
    
    def update_folder_name(self, user_email, old_name, new_name):
        """폴더 이름 변경 (호환성)"""
        folders = self.get_user_folders(user_email)
        for folder in folders:
            if folder.get('title') == old_name:
                return self.update_folder(folder['folder_id'], title=new_name) is not None
        return False
    
    def delete_folder_by_name(self, user_email, folder_name):
        """폴더 삭제 (호환성)"""
        folders = self.get_user_folders(user_email)
        for folder in folders:
            if folder.get('title') == folder_name:
                return self.delete_folder(folder['folder_id'])
        return False
