"""Shared Streamlit navigation — used by both app.py and streamlit_app.py."""
import streamlit as st
from web.auth import check_auth


def run_app():
    """Configure and launch the Streamlit multi-page app."""
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
