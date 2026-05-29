"""纯 Streamlit 入口（无 FastAPI 干扰）

用法: streamlit run web/streamlit_app.py
"""
import sys, os

# 显式加载 .env 到 os.environ（必须在 import settings 之前）
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(_env_path, override=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from config.settings import settings
from web.auth import check_auth

def run():
    st.set_page_config(page_title="攸县有话说", layout="wide", page_icon="🎬")
    check_auth()

    from web.pages.create import render_create_page
    from web.pages.review import render_review_page
    from web.pages.publish import render_publish_page
    from web.pages.dashboard import render_dashboard_page
    from web.pages.settings import render_settings_page

    create_page = st.Page(render_create_page, title="选题共创", icon=":material/lightbulb:", default=True)
    review_page = st.Page(render_review_page, title="审核中心", icon=":material/rate_review:")
    publish_page = st.Page(render_publish_page, title="发布管理", icon=":material/publish:")
    dashboard_page = st.Page(render_dashboard_page, title="数据看板", icon=":material/dashboard:")
    settings_page = st.Page(render_settings_page, title="模型设置", icon=":material/settings:")

    pg = st.navigation([create_page, review_page, publish_page, dashboard_page, settings_page])
    pg.run()

if __name__ == "__main__":
    run()
