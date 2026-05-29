"""Shared Streamlit navigation — used by both app.py and streamlit_app.py."""
import asyncio
import logging
import sys
import urllib.parse
from pathlib import Path

# MPA 模式下确保项目根目录在 sys.path 中
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
from web.auth import check_auth
from web.styles import inject_styles, COLORS, render_logo

logger = logging.getLogger(__name__)

# ── SVG favicon ──
_FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 36 36">'
    '<rect width="36" height="36" rx="10" fill="#E07A5F"/>'
    '<text x="18" y="25" text-anchor="middle" fill="white" '
    'font-size="18" font-weight="700" font-family="sans-serif">攸</text>'
    '</svg>'
)
FAVICON = "data:image/svg+xml," + urllib.parse.quote(_FAVICON_SVG)


def _load_sidebar_counts() -> dict:
    """从数据库加载侧边栏计数摘要。"""
    try:
        import aiosqlite
        from web.database import DB_PATH

        async def _query():
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = None
                cur = await db.execute(
                    "SELECT status, COUNT(*) FROM videos GROUP BY status"
                )
                rows = await cur.fetchall()
                return {row[0]: row[1] for row in rows}

        return asyncio.run(_query())
    except Exception:
        logger.exception("侧边栏计数查询失败")
        return {}


def run_app():
    """Configure and launch the Streamlit multi-page app."""
    st.set_page_config(
        page_title="攸县有话说 — AI 方言短视频生产平台",
        layout="wide",
        page_icon=FAVICON,
    )
    inject_styles()
    check_auth()

    # ── 侧边栏品牌区 ──
    logo = render_logo(36)
    with st.sidebar:
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:0.6rem;
            padding:0.5rem 0 0.75rem; border-bottom:1px solid {COLORS['border']};
            margin-bottom:0.75rem;">
            {logo}
            <div>
                <div style="font-size:1.1rem; font-weight:700; color:{COLORS['fg']};
                    line-height:1.2;">攸县有话说</div>
                <div style="font-size:0.7rem; color:{COLORS['muted']};">视频生产管理</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        counts = _load_sidebar_counts()
        pending_review = counts.get("pending_review", 0)
        approved = counts.get("approved", 0)
        if pending_review or approved:
            parts = []
            if pending_review:
                parts.append(f"{pending_review} 待审核")
            if approved:
                parts.append(f"{approved} 待发布")
            st.markdown(f"""
            <div style="background:{COLORS['bg_deep']}; border-radius:8px;
                padding:0.45rem 0.75rem; margin-bottom:0.75rem; font-size:0.8rem;
                color:{COLORS['muted']}; border:1px solid {COLORS['border']};">
                {"&nbsp;·&nbsp;".join(parts)}
            </div>
            """, unsafe_allow_html=True)

    # ── 页面注册 ──
    from web.pages.workspace import render_workspace_page
    from web.pages.create import render_create_page
    from web.pages.review import render_review_page
    from web.pages.publish import render_publish_page
    from web.pages.dashboard import render_dashboard_page
    from web.pages.settings import render_settings_page

    workspace_page = st.Page(
        render_workspace_page, title="工作台",
        icon=":material/dashboard:", default=True,
    )
    create_page = st.Page(
        render_create_page, title="选题共创",
        icon=":material/lightbulb:",
    )
    review_page = st.Page(
        render_review_page, title="视频审核",
        icon=":material/rate_review:",
    )
    publish_page = st.Page(
        render_publish_page, title="发布中心",
        icon=":material/publish:",
    )
    dashboard_page = st.Page(
        render_dashboard_page, title="数据洞察",
        icon=":material/bar_chart:",
    )
    settings_page = st.Page(
        render_settings_page, title="系统设置",
        icon=":material/settings:",
    )

    pg = st.navigation([
        workspace_page, create_page, review_page,
        publish_page, dashboard_page, settings_page,
    ])
    pg.run()

    with st.sidebar:
        st.markdown("---")
        st.caption("攸县有话说 v2.0")


if __name__ == "__main__":
    run_app()
