"""FastAPI backend + Streamlit frontend entrypoint.

For Streamlit UI (recommended):
  streamlit run web/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

For FastAPI backend:
  uvicorn web.app:app --reload

For combined (dev only, port conflicts possible):
  cd /home/liuzl/agent/YouXian-Says && streamlit run web/app.py
"""
import sys, os
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
from contextlib import asynccontextmanager
from fastapi import FastAPI
from config.settings import settings
from web.auth import check_auth

# ── FastAPI Setup ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: verify database is accessible on startup."""
    try:
        import aiosqlite
        async with aiosqlite.connect("data/youxian.db") as db:
            await db.execute("SELECT 1")
        print("✓ Database accessible")
    except Exception as e:
        print(f"⚠ Database not ready: {e}. Run: python scripts/init_db.py")
    yield

app = FastAPI(title="攸县有话说 API", version="0.1.0", lifespan=lifespan)

# Register routers
from web.routers import auth, topics, scripts, videos
app.include_router(auth.router)
app.include_router(topics.router)
app.include_router(scripts.router)
app.include_router(videos.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ── Streamlit Entrypoint ──

def run_streamlit():
    st.set_page_config(page_title="攸县有话说", layout="wide", page_icon="🎬")

    # Auth guard
    check_auth()

    # Navigation (Phase 5: all 5 admin pages)
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


# When run directly with `streamlit run web/app.py`
if __name__ == "__main__":
    run_streamlit()
