# ai_learning_server.py
# AI 학습 지원 시스템 - 서버 (리팩토링된 버전)

import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Server.server_core import AILearningServer
from env_utils import DEFAULT_HOST, DEFAULT_PORT


def main():
    parser = argparse.ArgumentParser(description="AI 학습 지원 시스템 서버")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"서버 주소 (기본값: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"서버 포트 (기본값: {DEFAULT_PORT})")
    
    args = parser.parse_args()
    
    server = AILearningServer(host=args.host, port=args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n서버 종료 중...")
        server.stop()


if __name__ == "__main__":
    main()

