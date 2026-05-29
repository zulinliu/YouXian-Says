"""审核中心页面 — 分镜预览 + 视频播放 + 结构化审核"""
import streamlit as st


def render_review_page():
    st.title("审核中心")
    st.markdown("查看和审核视频，提供结构化修改意见。")

    tab1, tab2 = st.tabs(["待审核", "已审核"])

    with tab1:
        st.info("暂无待审核视频。完成选题→脚本→制作流程后，视频将出现在这里。")

        # Demo: show a mock review interface when data exists
        if st.session_state.get("confirmed_topic"):
            st.markdown("---")
            st.markdown("### 示例审核")
            st.video("output/final/mock_demo.mp4")

            with st.form("review_form"):
                st.markdown("#### 审核意见")
                action = st.radio("审核结果", ["通过 ✅", "轻微修改", "重新制作 ❌"], horizontal=True)

                if action != "通过 ✅":
                    st.multiselect(  # noqa: F841
                        "修改维度",
                        ["画面/B-roll", "配音/语气", "字幕/翻译", "背景音乐", "脚本内容"],
                    )
                    st.text_area("具体修改要求")  # noqa: F841

                if st.form_submit_button("提交审核", type="primary"):
                    st.toast(f"审核完成: {action}")

    with tab2:
        st.info("已审核视频将显示在此处。")
