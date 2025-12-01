# server_data.py
# 서버 데이터 관리 모듈

import os
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from env_utils import DATA_DIR


class ServerDataManager:
    """서버 데이터 관리 클래스"""
    
    def __init__(self):
        self.users_file = os.path.join(DATA_DIR, "users.json")
        self.folders_file = os.path.join(DATA_DIR, "folders.json")
        self.files_file = os.path.join(DATA_DIR, "files.json")
        
        # 디렉토리 생성
        self.ensure_directories()
        
        # 데이터 로드
        self.load_data()
    
    def ensure_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs(DATA_DIR, exist_ok=True)
    
    def load_data(self):
        """데이터 파일 로드"""
        # 사용자 데이터
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r', encoding='utf-8') as f:
                self.users = json.load(f)
        else:
            self.users = {}
        
        # 폴더 데이터
        if os.path.exists(self.folders_file):
            with open(self.folders_file, 'r', encoding='utf-8') as f:
                self.folders = json.load(f)
        else:
            self.folders = {}
        
        # 파일 데이터
        if os.path.exists(self.files_file):
            with open(self.files_file, 'r', encoding='utf-8') as f:
                self.files = json.load(f)
        else:
            self.files = {}
    
    def save_data(self):
        """데이터 파일 저장"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
        with open(self.folders_file, 'w', encoding='utf-8') as f:
            json.dump(self.folders, f, ensure_ascii=False, indent=2)
        with open(self.files_file, 'w', encoding='utf-8') as f:
            json.dump(self.files, f, ensure_ascii=False, indent=2)


