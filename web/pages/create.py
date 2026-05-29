"""选题共创页面 — 用户输入想法，AI发散选题，用户选择确认并持久化到 DB"""
import asyncio
import logging

import streamlit as st
from agents import ContentAgent
from web.styles import (
    COLORS, esc, icon, page_header, pipeline_progress,
    section_header,
)

logger = logging.getLogger(__name__)


CONFIRMED_STATUS = "topic_selected"


def _save_topic_to_db(title: str, pillar: str) -> int | None:
    """确认选题时创建 DB 记录：videos + topics 表。返回 video_id。"""
    try:
        import aiosqlite
        from web.database import DB_PATH

        async def _insert():
            async with aiosqlite.connect(DB_PATH) as db:
                cur = await db.execute(
                    "INSERT INTO videos (title, status) VALUES (?, ?)",
                    (title, CONFIRMED_STATUS),
                )
                video_id = cur.lastrowid
                await db.execute(
                    "INSERT INTO topics (video_id, title, pillar, source) "
                    "VALUES (?, ?, ?, 'ai_cocreate')",
                    (video_id, title, pillar or "未分类"),
                )
                await db.commit()
                return video_id

        return asyncio.run(_insert())
    except Exception:
        logger.exception("保存选题到数据库失败")
        return None


def _topic_card(idx: int, title: str, pillar: str, difficulty: str, selected: bool):
    border_left = f"border-left:3px solid {COLORS['primary']};" if selected else ""
    bg = COLORS["primary_light"] if selected else COLORS["card"]

    pillar_html = (
        f'<div style="font-size:0.8rem; color:{COLORS["muted"]};">'
        f'{icon("tag", "sm")} {esc(pillar)}</div>'
        if pillar else ""
    )

    st.markdown(f"""
    <div style="background:{bg}; border:1px solid {COLORS['border']};
        {border_left}border-radius:var(--yx-radius);
        padding:1.25rem; margin-bottom:0.5rem;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <div style="display:flex; gap:0.75rem; align-items:flex-start; flex:1;">
                <div style="background:{COLORS['primary']}; color:white; width:28px;
                    height:28px; border-radius:8px; display:inline-flex;
                    align-items:center; justify-content:center; font-size:0.8rem;
                    font-weight:600; flex-shrink:0;">{idx + 1}</div>
                <div style="flex:1;">
                    <div style="font-size:1.05rem; font-weight:600; color:{COLORS['fg']};
                        margin-bottom:0.25rem;">{esc(title)}</div>
                    {pillar_html}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_create_page():
    page_header("lightbulb", "选题共创", "输入想法，AI 为你发散多个角度的选题")

    if st.session_state.get("confirmed_topic"):
        pipeline_progress(CONFIRMED_STATUS)

    with st.container(border=True):
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:0.4rem; margin-bottom:0.5rem;">
            {icon('sparkle', 'sm', COLORS['primary'])}
            <span style="font-weight:600; color:{COLORS['fg']};">你的灵感</span>
        </div>
        """, unsafe_allow_html=True)
        user_idea = st.text_area(
            "你的想法",
            placeholder="例如：今天想聊聊攸县米粉",
            height=100,
            label_visibility="collapsed",
        )

        if st.button("发散创意", type="primary",
                     disabled=not user_idea, use_container_width=True):
            if not user_idea:
                st.warning("请先输入一个想法")
                return

            with st.spinner("AI 正在发散创意..."):
                agent = ContentAgent()
                topics = asyncio.run(agent.diverge_topics(user_idea))

            if not topics:
                st.error("AI 未生成选题，请重试")
                return

            st.success(f"已生成 {len(topics)} 个选题")
            st.session_state.topics = topics

    if "topics" in st.session_state:
        st.markdown(section_header("list", "选题列表", COLORS["accent"]),
                    unsafe_allow_html=True)
        selected_idx = st.session_state.get("selected_topic_idx", -1)

        for i, topic in enumerate(st.session_state.topics):
            title = topic.get("title", topic.get("name", f"选题 {i+1}"))
            pillar = topic.get("pillar", topic.get("category", ""))
            difficulty = topic.get("difficulty", topic.get("heat_prediction", ""))
            is_selected = i == selected_idx

            _topic_card(i, title, pillar, difficulty, is_selected)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("选择", key=f"select_{i}", use_container_width=True):
                    st.session_state.selected_topic = topic
                    st.session_state.selected_topic_idx = i
                    st.toast(f"已选择: {title}")
            with col2:
                if st.button("确认选题", key=f"confirm_{i}",
                             type="primary", use_container_width=True):
                    video_id = _save_topic_to_db(title, pillar)
                    if video_id is None:
                        st.error("保存失败，请重试")
                        return
                    st.session_state.confirmed_topic = {
                        **topic, "video_id": video_id,
                    }
                    st.toast(f"选题已确认并保存: {title}",
                             icon=":material/check_circle:")
                    st.info("选题已保存到数据库，可在工作台查看生产进度")
