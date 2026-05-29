"""纯 Streamlit 入口（无 FastAPI 干扰）

用法: streamlit run web/streamlit_app.py
"""
import sys, os

# 显式加载 .env 到 os.environ（必须在 import settings 之前）
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(_env_path, override=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.navigation import run_app

if __name__ == "__main__":
    run_app()
