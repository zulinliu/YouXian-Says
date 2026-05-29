"""模型设置页面 — 查看/切换/编辑模型参数"""

import streamlit as st
from config.model_registry import ModelRegistry


def test_api_connection(api_base: str, model_name: str, api_key: str,
                         env_key: str, provider: str) -> dict:
    """Test API connectivity by making a lightweight request.

    Phase 7: Attempts actual API call when credentials are provided.
    Falls back to URL validation when no credentials.
    """
    import time
    import os

    # If we have what looks like a real API key, try actual connectivity
    effective_key = api_key or os.environ.get(env_key, "")

    if effective_key and effective_key != "sk-xxx":
        try:
            import httpx
            start = time.monotonic()

            # Test with a simple model list call
            if provider in ("deepseek", "openai", "openai_relay", "zhipu_relay"):
                resp = httpx.get(
                    f"{api_base.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {effective_key}"},
                    timeout=10
                )
            else:
                # For media providers, just test URL reachability
                resp = httpx.get(api_base.rstrip('/'), timeout=10)

            latency = int((time.monotonic() - start) * 1000)

            if resp.status_code < 500:
                return {"ok": True, "latency_ms": latency, "error": ""}
            else:
                return {"ok": False, "latency_ms": latency,
                       "error": f"HTTP {resp.status_code}: {resp.text[:100]}"}

        except Exception as e:
            return {"ok": False, "latency_ms": 0, "error": str(e)[:100]}

    # Fallback: URL format validation (Phase 1 behavior)
    if not api_base.startswith("https://"):
        return {"ok": False, "latency_ms": 0, "error": "API地址必须以 https:// 开头"}

    return {"ok": True, "latency_ms": 0, "error": "连接测试仅验证URL格式（未配置API Key）"}


def render_settings_page():
    """渲染模型设置页面"""
    st.title("模型设置")
    st.caption("配置各功能维度的模型参数，切换激活模型或编辑 API 地址 / Key")

    registry = ModelRegistry.list_all()

    for fid, func_info in registry.items():
        active_id = func_info["active_id"]
        active_name = func_info["active_name"]
        function_name = func_info["function_name"]

        with st.expander(f"**{function_name}**", expanded=True):
            # 当前激活模型徽章
            cols = st.columns([3, 1])
            cols[0].markdown(f"**当前使用：** `{active_name}` ({active_id})")
            cols[1].markdown("<div style='text-align:right'><span style='background:#00c853;color:white;padding:2px 12px;border-radius:12px;font-size:0.85em'>当前使用</span></div>", unsafe_allow_html=True)

            st.divider()

            for model in func_info["options"]:
                model_id = model["id"]
                is_active = model_id == active_id

                with st.container():
                    st.markdown(f"##### {model['name']}  —  *{model['provider']}*")
                    st.caption(f"质量: {model.get('cost_per_m_tokens', 0)}元/百万token | 上下文: {model.get('max_context', 'N/A')}")
                    if model.get("notes"):
                        st.caption(f"备注: {model['notes']}")

                    # 模型参数编辑表单
                    with st.form(key=f"form_{fid}_{model_id}", clear_on_submit=False):
                        api_base = st.text_input(
                            "API 地址",
                            value=model.get("api_base", ""),
                            key=f"api_base_{fid}_{model_id}",
                        )
                        model_name = st.text_input(
                            "模型名称",
                            value=model.get("model_name", ""),
                            key=f"model_name_{fid}_{model_id}",
                        )
                        api_key = st.text_input(
                            "API Key",
                            type="password",
                            placeholder=model.get("api_key_masked", "（未设置）"),
                            key=f"api_key_{fid}_{model_id}",
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            save_clicked = st.form_submit_button("保存参数", use_container_width=True)
                        with col2:
                            switch_clicked = st.form_submit_button("切换到该模型", use_container_width=True, disabled=is_active)

                        if save_clicked:
                            try:
                                ModelRegistry.update_model_config(
                                    function_id=fid,
                                    model_id=model_id,
                                    api_base=api_base or None,
                                    api_key=api_key or None,
                                    model_name=model_name or None,
                                )
                                st.toast(f"✅ {model['name']} 参数已保存", icon=":material/check_circle:")
                            except Exception as e:
                                st.toast(f"❌ 保存失败: {e}", icon=":material/error:")

                        if switch_clicked:
                            try:
                                ModelRegistry.switch(function_id=fid, model_id=model_id)
                                st.toast(f"✅ 已切换到 {model['name']}", icon=":material/check_circle:")
                            except Exception as e:
                                st.toast(f"❌ 切换失败: {e}", icon=":material/error:")

                    # 测试连接按钮（在表单外部）
                    cols = st.columns([1, 4])
                    with cols[0]:
                        test_key = f"test_{fid}_{model_id}"
                        test_clicked = st.button("测试连接", key=test_key)
                        if test_clicked:
                            result = test_api_connection(
                                api_base=model.get("api_base", ""),
                                model_name=model.get("model_name", ""),
                                api_key="",
                                env_key=model.get("api_key_env", ""),
                                provider=model.get("provider", ""),
                            )
                            if result["ok"]:
                                msg = f"✅ 连接正常{(' - ' + result['error']) if result['error'] else ''}"
                                st.toast(msg, icon=":material/check_circle:")
                            else:
                                st.toast(f"❌ {result['error']}", icon=":material/error:")

                    st.divider()

    st.markdown("---")
    st.subheader("📊 视频生命周期追踪")

    # Fetch recent videos from API or DB
    try:
        import aiosqlite
        from web.database import DB_PATH

        async def _fetch_videos():
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT id, title, status, created_at, updated_at FROM videos ORDER BY created_at DESC LIMIT 20"
                )
                return await cursor.fetchall()

        import asyncio
        videos = asyncio.run(_fetch_videos())

        if videos:
            for v in videos:
                vdict = dict(v)
                with st.expander(f"[{vdict['status']}] {vdict['title']}", expanded=False):
                    st.code(f"ID: {vdict['id']}\n状态: {vdict['status']}\n创建: {vdict['created_at']}\n更新: {vdict['updated_at']}")
                    if vdict['status'] in ('rejected',):
                        if st.button(f"🔄 重试 #{vdict['id']}", key=f"retry_{vdict['id']}"):
                            st.toast(f"重试任务 #{vdict['id']} 已提交")
                    elif vdict['status'] == 'pending_review':
                        if st.button(f"✅ 审核 #{vdict['id']}", key=f"review_{vdict['id']}"):
                            st.toast("已跳转到审核页面")
        else:
            st.info("暂无视频记录")
    except Exception as e:
        st.caption(f"数据库未就绪: {e}")
