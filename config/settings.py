"""系统配置 — 从.env加载所有API Key和参数"""

import os as _os
import secrets as _secrets

from dotenv import load_dotenv as _load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，从.env文件加载"""

    # ── DeepSeek ──
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    # ── MiniMax ──
    minimax_api_key: str = ""
    minimax_group_id: str = ""

    # ── Xiaomi MiMo ──
    mimo_api_key: str = ""
    mimo_base_url: str = "https://api.xiaomimimo.com"

    # ── New API 中转站兼容通道 ──
    openai_relay_api_key: str = ""
    openai_relay_base_url: str = ""
    anthropic_relay_api_key: str = ""
    anthropic_relay_base_url: str = ""
    glm_relay_api_key: str = ""
    glm_relay_base_url: str = ""

    # ── 官方海外API（仅后续购买后启用） ──
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # ── 图像外部横评候选 ──
    firefly_api_key: str = ""
    seedream_api_key: str = ""
    flux_api_key: str = ""

    # ── HeyGen ──
    heygen_api_key: str = ""
    heygen_avatar_id: str = ""
    heygen_plan: str = "creator"

    # ── 视频横评候选 ──
    kling_access_key: str = ""
    kling_secret_key: str = ""
    runway_api_key: str = ""
    google_cloud_project: str = ""
    luma_api_key: str = ""
    pika_api_key: str = ""

    # ── 外部语音/数字人横评候选 ──
    elevenlabs_api_key: str = ""
    cartesia_api_key: str = ""
    openai_tts_api_key: str = ""
    tavus_api_key: str = ""
    d_id_api_key: str = ""
    akool_api_key: str = ""

    # ── Web ──
    admin_password: str  # 无默认值，必须在.env中设置
    web_port: int = 8501

    # ── n8n工作流引擎 ──
    n8n_webhook_url: str = "http://localhost:5678/webhook"

    # ── 检索与对象存储 ──
    search_api_key: str = ""
    object_storage_endpoint: str = ""
    object_storage_bucket: str = "youxian-video"
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""

    # ── 易媒（发布平台） ──
    yimei_username: str = ""
    yimei_password: str = ""

    # ── 数据分析 ──
    chanmama_token: str = ""

    # ── 数据加密 ──
    master_encryption_key: str = ""

    # ── JWT ──
    jwt_secret_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

# 确保 .env 已加载到 os.environ（供 model_registry 等模块通过 os.environ.get 读取）
_load_dotenv(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", ".env"))

# 如果未配置 JWT 密钥，自动生成一个（仅限本次运行）
if not settings.jwt_secret_key:
    settings.jwt_secret_key = _secrets.token_urlsafe(64)

# 启动时校验管理员密码安全性
if settings.admin_password in ("admin", ""):
    raise ValueError(
        "请在.env中设置安全的ADMIN_PASSWORD，不允许使用默认值"
    )
