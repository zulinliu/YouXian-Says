"""选题共创页面 — 用户输入想法，AI发散选题，用户选择确认"""
import streamlit as st
from agents import ContentAgent


def render_create_page():
    st.title("选题共创")
    st.markdown("输入一个想法或关键词，AI 将为你发散多个角度的选题。")

    user_idea = st.text_area(
        "你的想法",
        placeholder="例如：今天想聊聊攸县米粉",
        height=100,
    )

    if st.button("发散创意", type="primary", disabled=not user_idea):
        if not user_idea:
            st.warning("请先输入一个想法")
            return

        with st.spinner("AI 正在发散创意..."):
            agent = ContentAgent()
            import asyncio
            topics = asyncio.run(agent.diverge_topics(user_idea))

        if not topics:
            st.error("AI 未生成选题，请重试")
            return

        st.success(f"已生成 {len(topics)} 个选题")
        st.session_state.topics = topics

    if "topics" in st.session_state:
        st.markdown("### 选题列表")
        for i, topic in enumerate(st.session_state.topics):
            title = topic.get("title", topic.get("name", f"选题 {i+1}"))
            pillar = topic.get("pillar", topic.get("category", ""))
            difficulty = topic.get("difficulty", topic.get("heat_prediction", ""))

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{title}**")
                    if pillar:
                        st.caption(f"角度: {pillar}")
                with col2:
                    if difficulty:
                        st.caption(f"难度: {'⭐' * int(difficulty)}")
                with col4:
                    if st.button(f"选择", key=f"select_{i}"):
                        st.session_state.selected_topic = topic
                        st.session_state.selected_topic_idx = i
                        st.toast(f"已选择: {title}")

            if st.button("确认选题", key=f"confirm_{i}", type="primary"):
                st.session_state.confirmed_topic = topic
                st.success(f"已确认选题: {title}")
                st.info("选题已确认，后续可进入脚本生成流程（Phase 6+）")
