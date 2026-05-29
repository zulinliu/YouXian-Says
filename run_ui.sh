#!/usr/bin/env bash
# 启动 Streamlit 管理后台（不加载 FastAPI）
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true
echo "=== 攸县有话说 - 管理后台 ==="
echo "启动中..."
echo "访问地址: http://0.0.0.0:8501"
streamlit run web/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
