"""发布中心页面 — 待确认队列 + 平台选择 + 确认发布"""
import asyncio
import logging

import streamlit as st
from web.styles import (
    COLORS, esc, icon, page_header, empty_state,
    pipeline_progress, badge, section_header,
)

logger = logging.getLogger(__name__)


def _load_publish_queue() -> list[dict]:
    """从数据库加载待发布视频。"""
    try:
        import aiosqlite
        from web.database import DB_PATH

        async def _query():
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT id, title, status, created_at, updated_at "
                    "FROM videos WHERE status = 'approved' "
                    "ORDER BY created_at DESC"
                )
                return [dict(row) for row in await cursor.fetchall()]

        return asyncio.run(_query())
    except Exception:
        logger.exception("加载待发布队列失败")
        return []


def _load_published() -> list[dict]:
    """从数据库加载已发布视频。"""
    try:
        import aiosqlite
        from web.database import DB_PATH

        async def _query():
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT id, title, status, created_at, updated_at "
                    "FROM videos WHERE status = 'published' "
                    "ORDER BY updated_at DESC LIMIT 20"
                )
                return [dict(row) for row in await cursor.fetchall()]

        return asyncio.run(_query())
    except Exception:
        logger.exception("加载已发布视频失败")
        return []


def _platform_badge(icon_name: str, name: str, active: bool = False):
    border = COLORS["primary"] if active else COLORS["border"]
    bg = COLORS["primary_light"] if active else COLORS["card"]
    ic = icon(icon_name, "lg", COLORS["primary"] if active else COLORS["muted"])
    return f"""
    <div style="background:{bg}; border:1px solid {border};
        border-radius:var(--yx-radius-sm); padding:0.75rem 1.25rem;
        text-align:center; min-width:80px;">
        <div>{ic}</div>
        <div style="font-size:0.8rem; color:{COLORS['fg']};
            font-weight:500; margin-top:0.25rem;">{esc(name)}</div>
    </div>
    """


def render_publish_page():
    page_header("rocket", "发布中心", "管理待发布视频，多平台一键分发")

    tab1, tab2 = st.tabs(["待发布队列", "已发布"])

    with tab1:
        queue = _load_publish_queue()
        video = queue[0] if queue else None

        if not video:
            empty_state("rocket", "暂无待发布视频",
                        "审核通过后，视频将出现在这里")
        else:
            pipeline_progress(video["status"])
            col_preview, col_form = st.columns([2, 3])

            with col_preview:
                video_path = f"output/final/{video['id']}.mp4"
                try:
                    st.video(video_path)
                except Exception:
                    st.markdown(f"""
                    <div style="background:{COLORS['card']};
                        border-radius:var(--yx-radius); aspect-ratio:9/16;
                        display:flex; align-items:center; justify-content:center;
                        border:1px solid {COLORS['border']}; max-height:400px;">
                        <div style="text-align:center; color:{COLORS['muted']};">
                            <div style="margin-bottom:0.25rem;">
                                {icon('film', 'xl', COLORS['muted_light'])}
                            </div>
                            <div>视频预览</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            with col_form:
                st.markdown(f"### {esc(video['title'])}")

                st.markdown(section_header("link", "目标平台", COLORS["accent"]),
                            unsafe_allow_html=True)
                st.markdown(f"""
                <div style="display:flex; gap:0.75rem; margin-bottom:1rem;">
                    {_platform_badge('tiktok', '抖音', True)}
                    {_platform_badge('wechat', '视频号', True)}
                </div>
                """, unsafe_allow_html=True)

                with st.form("publish_form"):
                    platforms = st.multiselect(
                        "选择发布平台",
                        ["抖音", "视频号"],
                        default=["抖音", "视频号"],
                        label_visibility="collapsed",
                        help="MVP 阶段支持抖音和视频号",
                    )
                    schedule_type = st.radio(
                        "发布时间", ["立即发布", "定时发布"],
                        horizontal=True,
                    )
                    if schedule_type == "定时发布":
                        st.date_input("发布日期")

                    st.markdown("---")
                    st.markdown(section_header("clip", "发布确认", COLORS["primary"]),
                                unsafe_allow_html=True)

                    review_title = st.text_input(
                        "视频标题", value=video.get("title", ""))
                    st.text_input("标签（逗号分隔）", value="攸县话,方言")
                    st.text_area("描述")

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button(
                            "确认发布", type="primary",
                            use_container_width=True)
                    with col2:
                        st.form_submit_button("取消", use_container_width=True)

                    if submitted:
                        try:
                            import aiosqlite
                            from web.database import DB_PATH

                            async def _update():
                                async with aiosqlite.connect(DB_PATH) as db:
                                    await db.execute(
                                        "UPDATE videos SET status = 'publishing' "
                                        "WHERE id = ? AND status = 'approved'",
                                        (video["id"],),
                                    )
                                    await db.commit()

                            asyncio.run(_update())
                            st.toast(f"已提交发布: {review_title}",
                                     icon=":material/check_circle:")
                            st.success(f"发布任务已提交: {', '.join(platforms)}")
                        except Exception as e:
                            logger.exception("发布提交失败")
                            st.error(f"发布提交失败: {e}")

            if len(queue) > 1:
                with st.expander(f"队列中还有 {len(queue) - 1} 个视频"):
                    for qv in queue[1:]:
                        st.markdown(f"- {esc(qv['title'])}")

    with tab2:
        published = _load_published()
        if not published:
            empty_state("trophy", "暂无已发布的视频",
                        "已发布的视频将在此处展示")
        else:
            for pv in published:
                with st.expander(esc(pv["title"]), expanded=False):
                    st.markdown(f"""
                    <div style="display:flex; gap:0.5rem; align-items:center;
                        margin-bottom:0.5rem;">
                        {badge('已发布', COLORS['success'])}
                    </div>
                    <div style="font-size:0.8rem; color:{COLORS['muted']};">
                        发布: {esc(str(pv['updated_at']))}
                    </div>
                    """, unsafe_allow_html=True)
