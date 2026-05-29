#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== 攸县方言短视频系统 - 一键安装 ==="

# Check Python version
PYTHON="python3"
if ! command -v $PYTHON &>/dev/null; then
    echo "ERROR: Python3 not found"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
echo "OK: $PYTHON_VERSION"

# Check FFmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "WARNING: ffmpeg not found. Install with: sudo apt install ffmpeg"
else
    echo "OK: ffmpeg found ($(ffmpeg -version | head -1))"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
cd "$PROJECT_DIR"
$PYTHON -m venv venv

# Activate and install dependencies
echo ""
echo "Installing dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Copy .env.example to .env if not exists
if [ ! -f .env ]; then
    cp -n .env.example .env 2>/dev/null || true
    echo ""
    echo "Created .env from .env.example"
fi

echo ""
echo "=== 安装完成 ==="
echo ""
echo "下一步："
echo "  1. 编辑 .env 文件配置 API Key："
echo "     vi .env"
echo ""
echo "  2. 启动 Streamlit 管理后台："
echo "     source venv/bin/activate"
echo "     streamlit run web/app.py"
echo ""
echo "  3. 访问 http://localhost:8501 登录（默认密码见 .env 中的 ADMIN_PASSWORD）"
echo ""
