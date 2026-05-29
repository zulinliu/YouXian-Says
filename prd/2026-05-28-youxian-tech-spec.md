# 攸县方言短视频系统 — 技术实施规格

> 本文档是 AI agent 可直接按步骤搭建的技术蓝图。
> 设计日期：2026-05-28
> 状态：已通过评审
> 前置文档：`2026-05-28-youxian-dialect-video-design.md`
> 模型/Agent/工具最新优化：见 `2026-05-28-model-agent-tool-optimization.md`

## 0.1 评审后技术修订决策（2026-05-28）

| 技术项 | 修订后要求 |
|---|---|
| MVP范围 | 先支持每周3条，优先抖音和视频号；四平台日更作为后续扩展 |
| 媒体模型采购 | 搭建期不强依赖 HeyGen/Runway；先实现配置、适配器、Mock/本地占位流程 |
| 数字人 | 先虚拟本地人设，`digital_human.py` 必须支持 `mock/local/manual/heygen` 四种模式 |
| B-roll | `video_gen.py` 必须支持 `mock/local/runway/veo/kling/luma/pika/hailuo`，未采购时不阻塞合成 |
| 声音 | 默认本人 MiMo 声音克隆；其他人声音需要新增授权记录字段 |
| 发布 | 默认进入待确认队列；无人值守发布必须有稳定数据后再开启开关 |
| 事实来源 | 明确事实尽量记录来源；爆款演绎和民间说法用风险分级，不作为生成阻塞 |

---

## 一、系统架构

```
┌──────────────────────────────────────────────────────┐
│                  Web 管理后台 (Streamlit)              │
│                                                      │
│  /create    → 选题共创（用户提供idea，AI发散）          │
│  /review    → 分镜审核 + 视频审核（用户审阅打回）       │
│  /publish   → 发布管理（确认分发）                     │
│  /dashboard → 数据看板（自动更新）                     │
│                                                      │
└──────────────────────┬───────────────────────────────┘
                       │ REST API
┌──────────────────────┴───────────────────────────────┐
│              FastAPI 后端 + n8n 工作流编排              │
│                                                      │
│  /api/topics      → 选题 CRUD + AI创意生成            │
│  /api/scripts     → 脚本 CRUD + AI自动生成            │
│  /api/storyboards → 分镜 CRUD + AI自动生成            │
│  /api/voices      → 配音任务提交 + 状态查询            │
│  /api/videos      → 视频合成任务 + 状态查询            │
│  /api/publish     → 发布任务 + 状态查询               │
│  /api/analytics   → 数据采集 + 分析报告               │
│                                                      │
└──────────────────────┬───────────────────────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     ▼                 ▼                 ▼
┌──────────┐    ┌──────────┐     ┌──────────┐
│ 内容Agent │    │ 制作Agent │     │ 运营Agent │
│          │    │          │     │          │
│ DeepSeek │    │ MiMo TTS │     │ 蝉妈妈    │
│ GLM/GPT  │    │ Mock/HeyGen│     │ 易媒/API  │
│ GPT-img2 │    │ Mock/Runway │   │ GLM/DS   │
│          │    │ FFmpeg   │     │          │
└──────────┘    └──────────┘     └──────────┘
```

## 二、项目目录结构

```
./
├── config/
│   ├── settings.py          # 所有API Key和配置
│   ├── model_registry.py    # 模型注册中心（多模型+切换）
│   └── prompts.py           # LLM提示词模板
├── agents/
│   ├── content_agent.py     # 内容Agent（选题+脚本+分镜）
│   ├── production_agent.py  # 制作Agent（配音+数字人+合成）
│   ├── ops_agent.py         # 运营Agent（发布+数据）
│   └── revision_parser.py   # 修改意见解析器（自然语言→结构化操作）
├── services/
│   ├── llm.py               # DeepSeek/MiMo/GLM/GPT中转 API封装（MiniMax仅基线）
│   ├── voice.py             # 语音克隆API封装（MiMo TTS主线/外部横评/MiniMax最后兜底）
│   ├── digital_human.py     # 数字人封装：mock/local/manual/HeyGen/Tavus/D-ID/AKOOL
│   ├── video_gen.py         # 视频生成封装：mock/local/Runway/Veo/Kling/Luma/Pika/Hailuo
│   ├── image_gen.py         # GPT-image-2 Relay / 外部图像横评 / MiniMax image-01兜底 API封装
│   ├── composer.py          # FFmpeg视频合成
│   └── publisher.py         # 多平台发布
├── web/
│   ├── app.py               # FastAPI主应用
│   ├── auth.py              # 认证中间件（Streamlit登录 + FastAPI JWT）
│   ├── models.py            # 数据模型
│   ├── database.py          # SQLite数据库
│   └── pages/
│       ├── create.py        # 选题共创页
│       ├── review.py        # 审核页
│       ├── publish.py       # 发布页
│       ├── dashboard.py     # 数据看板
│       └── settings.py      # 模型切换设置页
├── templates/
│   ├── branding/            # 品牌元素（片头片尾水印）
│   ├── music/               # 背景音乐库
│   └── fonts/               # 字体文件
├── output/
│   ├── voices/              # 生成的配音文件
│   ├── videos/              # 生成的视频文件
│   ├── images/              # 生成的图片文件
│   └── final/               # 最终成品
├── data/
│   ├── youxian.db           # SQLite数据库
│   ├── dialect_dict.json    # 方言词典
│   └── knowledge_base.md    # 攸县知识库
├── tests/
│   ├── test_model_registry.py
│   ├── test_services/
│   │   ├── test_llm.py
│   │   ├── test_voice.py
│   │   └── test_composer.py
│   └── test_agents/
│       └── test_content_agent.py
├── scripts/
│   ├── setup.sh             # 一键安装脚本
│   ├── setup_voice_profile.py # 上传/登记声音克隆参考音频（不做本地训练）
│   └── daily_run.py         # 每日自动执行入口
├── requirements.txt
├── .env.example
└── README.md
```

## 三、配置文件

### 3.1 `.env.example`

```env
# DeepSeek
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# MiniMax
MINIMAX_API_KEY=xxx
MINIMAX_GROUP_ID=xxx

# Xiaomi MiMo
MIMO_API_KEY=xxx
MIMO_BASE_URL=https://api.xiaomimimo.com

# New API 中转站兼容通道（效果按模型本身评估，需单独监控稳定性/计费/API差异）
OPENAI_RELAY_API_KEY=sk-xxx
OPENAI_RELAY_BASE_URL=https://your-relay.example.com/v1
ANTHROPIC_RELAY_API_KEY=sk-ant-xxx
ANTHROPIC_RELAY_BASE_URL=https://your-relay.example.com/v1
GLM_RELAY_API_KEY=sk-xxx
GLM_RELAY_BASE_URL=https://your-relay.example.com/v1

# 如后续购买官方海外API，再单独启用
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# 图像外部横评候选（GPT-image-2为主线；这些只在版权/风格/成本需要时小额启用）
FIREFLY_API_KEY=
SEEDREAM_API_KEY=
FLUX_API_KEY=

# HeyGen
HEYGEN_API_KEY=xxx
HEYGEN_AVATAR_ID=xxx
HEYGEN_PLAN=creator              # 按当前官网积分套餐核算，启动前确认API权限和额度

# 视频横评候选（Runway/Veo/Kling/Luma/Pika优先；Hailuo仅作为已购兜底/基线）
KLING_ACCESS_KEY=xxx
KLING_SECRET_KEY=xxx
RUNWAY_API_KEY=xxx
GOOGLE_CLOUD_PROJECT=xxx
LUMA_API_KEY=xxx
PIKA_API_KEY=xxx

# 外部语音横评候选（MiMo低于门槛或需要更强情绪/角色声线时启用；MiniMax最后兜底）
ELEVENLABS_API_KEY=xxx
CARTESIA_API_KEY=xxx
OPENAI_TTS_API_KEY=xxx

# 数字人横评候选
TAVUS_API_KEY=xxx
D_ID_API_KEY=xxx
AKOOL_API_KEY=xxx

# 易媒（如无API则用手动）
YIMEI_USERNAME=xxx
YIMEI_PASSWORD=xxx

# 数据分析
CHANMAMA_TOKEN=xxx
SEARCH_API_KEY=xxx

# 对象存储（给HeyGen/视频模型提供可访问URL）
OBJECT_STORAGE_ENDPOINT=xxx
OBJECT_STORAGE_BUCKET=youxian-video
OBJECT_STORAGE_ACCESS_KEY=xxx
OBJECT_STORAGE_SECRET_KEY=xxx

# Web后台
ADMIN_PASSWORD=your_secure_password
WEB_PORT=8501

# n8n工作流引擎
N8N_WEBHOOK_URL=http://localhost:5678/webhook
```

### 3.2 `config/settings.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DeepSeek
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"

    # MiniMax
    minimax_api_key: str = ""
    minimax_group_id: str = ""

    # Xiaomi MiMo
    mimo_api_key: str = ""
    mimo_base_url: str = "https://api.xiaomimimo.com"

    # New API 中转站兼容通道
    openai_relay_api_key: str = ""
    openai_relay_base_url: str = ""
    anthropic_relay_api_key: str = ""
    anthropic_relay_base_url: str = ""
    glm_relay_api_key: str = ""
    glm_relay_base_url: str = ""

    # 官方海外API（仅后续购买后启用）
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # 图像外部横评候选
    firefly_api_key: str = ""
    seedream_api_key: str = ""
    flux_api_key: str = ""

    # HeyGen
    heygen_api_key: str = ""
    heygen_avatar_id: str = ""
    heygen_plan: str = "creator"  # 按当前官网积分套餐核算，启动前需确认API权限和月度额度

    # 视频横评候选
    kling_access_key: str = ""
    kling_secret_key: str = ""
    runway_api_key: str = ""
    google_cloud_project: str = ""
    luma_api_key: str = ""
    pika_api_key: str = ""

    # 外部语音/数字人横评候选
    elevenlabs_api_key: str = ""
    cartesia_api_key: str = ""
    openai_tts_api_key: str = ""
    tavus_api_key: str = ""
    d_id_api_key: str = ""
    akool_api_key: str = ""

    # Web
    admin_password: str  # 无默认值，必须在.env中设置，启动时校验安全性
    web_port: int = 8501

    # n8n工作流引擎
    n8n_webhook_url: str = "http://localhost:5678/webhook"

    # 检索与对象存储
    search_api_key: str = ""
    object_storage_endpoint: str = ""
    object_storage_bucket: str = "youxian-video"
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

# 启动时校验管理员密码安全性
if settings.admin_password in ("admin", ""):
    raise ValueError("⚠️ 请在.env中设置安全的ADMIN_PASSWORD，不允许使用默认值")
```

## 四、模型注册中心（可视化灵活切换）

### 4.1 设计思路

每个功能维度注册多个可用模型，Web后台下拉框切换，改完即生效，无需改代码。

2026-05-28 复核后，模型中心需要从“按功能维度手动切换”升级为“按任务场景自动路由”。原有下拉切换仍保留给管理员，但 Agent 默认通过 `ModelRouter` 选择模型：

- 批量低风险任务：优先 DeepSeek V4 Flash、MiMo V2.5、GLM-5.1 轻量调用；MiniMax M2.7 仅作为基线对照
- 深度推理任务：优先级固定为 GLM-5.1 → GPT-5.5 → DeepSeek V4 Pro
- 图像生产任务：优先 GPT-image-2，Firefly/Imagen/Seedream/FLUX 作为横评候选，MiniMax image-01 仅最后兜底
- 语音生产任务：优先 MiMo VoiceClone/VoiceDesign/TTS，其次 ElevenLabs/Cartesia/OpenAI TTS 横评，MiniMax Speech 2.8 仅最后兜底
- 视频和数字人任务：按效果/成本/稳定性全局排序，不按国内外或是否已购一刀切
- MiniMax 全系列模型：因实测效果相对不高，统一作为“已购兜底/基线对照/无合适选型时临时使用”，不得作为默认主链路第一或第二顺位
- New API 中转站模型：标记为 `channel=new_api_relay`，可进入主链路，但必须记录通道、失败率、延迟、计费和 API 兼容差异
- 账号凭证、Cookie、API Key：不传入任何生成模型；未公开商业数据按最小必要和 `data_policy` 控制

```
功能维度       可选模型A          可选模型B          可选模型C
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
文本草稿      DeepSeek V4 Flash MiMo V2.5        GLM-5.1轻量/MiniMax基线
深度推理      GLM-5.1 Relay     GPT-5.5 Relay    DeepSeek V4 Pro
多模态理解    MiMo Omni         GPT/Claude Relay  MiniMax M2.7基线
图像生成      GPT-image-2 Relay Firefly/Imagen    MiniMax image-01兜底
视频生成      Runway Gen-4      Veo/Kling/Luma/Pika  Hailuo基线兜底
语音克隆      MiMo VoiceClone  ElevenLabs/Cartesia MiniMax Speech2.8兜底
数字人        HeyGen           Tavus             D-ID/AKOOL
```

### 4.2 模型注册表定义

以下代码保留为基础注册表示例；生产实现应叠加 4.6 的 `channel`、`data_policy`、`api_compatibility`、`quality_tier` 和 `ModelRouter`，避免把通道选择、数据策略和模型能力混在一起。

```python
# config/model_registry.py

import os
import copy
import json
import base64
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

@dataclass
class ModelOption:
    """单个模型选项"""
    id: str               # 唯一标识，如 "deepseek_v4pro"
    name: str             # 显示名称，如 "DeepSeek V4 Pro"
    provider: str         # 厂商，如 "deepseek"
    api_base: str         # API端点（默认值，用户可在Web界面覆盖）
    model_name: str       # 模型调用名（默认值，用户可在Web界面覆盖）
    api_key_env: str      # 对应的.env变量名（后备方案）
    cost_per_m_tokens: float = 0  # 每百万token成本（元）
    max_context: int = 0          # 最大上下文
    channel: str = "official"     # official / new_api_relay / official_or_relay / local_tool
    modalities: list[str] = field(default_factory=list)
    quality_tier: str = "normal"  # draft / normal / high / flagship
    cost_tier: str = "normal"     # low / normal / high
    latency_tier: str = "normal"  # fast / normal / slow
    data_policy: str = "standard" # public_only / standard / sensitive_allowed / local_only
    api_compatibility: str = ""   # openai_chat / openai_responses / native / async_task
    supports_json: bool = False
    supports_tools: bool = False
    supports_image_edit: bool = False
    supports_reference_image: bool = False
    supports_9_16: bool = False
    fallback_ids: list[str] = field(default_factory=list)
    notes: str = ""               # 备注
    resolved_api_key: str = ""   # 运行时解析后的API Key（优先Web设置，其次.env）

@dataclass
class FunctionSlot:
    """一个功能维度的所有可选模型"""
    function_id: str      # 功能维度ID，如 "text_llm"
    function_name: str    # 功能维度名称，如 "文本LLM"
    options: list[ModelOption] = field(default_factory=list)
    active_id: str = ""   # 当前激活的模型ID

# ─── 全局模型注册表 ───

REGISTRY: dict[str, FunctionSlot] = {

    "text_llm": FunctionSlot(
        function_id="text_llm",
        function_name="文本LLM（选题/脚本/分镜/分析）",
        active_id="deepseek_v4_flash",
        options=[
            ModelOption(
                id="deepseek_v4_flash", name="DeepSeek V4 Flash",
                provider="deepseek", api_base="https://api.deepseek.com",
                model_name="deepseek-v4-flash", api_key_env="DEEPSEEK_API_KEY",
                cost_per_m_tokens=0, max_context=1_000_000,
                channel="official", modalities=["text", "tool"],
                quality_tier="draft", cost_tier="low", latency_tier="fast",
                api_compatibility="openai_chat", supports_json=True, supports_tools=True,
                notes="批量低成本任务：选题池、标题、标签、日报"
            ),
            ModelOption(
                id="deepseek_v4pro", name="DeepSeek V4 Pro",
                provider="deepseek", api_base="https://api.deepseek.com",
                model_name="deepseek-v4-pro", api_key_env="DEEPSEEK_API_KEY",
                cost_per_m_tokens=6, max_context=1_000_000,
                channel="official", modalities=["text", "tool"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="openai_chat", supports_json=True, supports_tools=True,
                notes="深度推理第三顺位；稳定中文定稿、脚本、分镜、周报"
            ),
            ModelOption(
                id="mimo_v2_5", name="MiMo V2.5",
                provider="xiaomi", api_base="https://api.xiaomimimo.com",
                model_name="mimo-v2.5", api_key_env="MIMO_API_KEY",
                cost_per_m_tokens=0, max_context=1_000_000,
                channel="official", modalities=["text", "tool"],
                quality_tier="draft", cost_tier="low",
                notes="批量低成本中文草稿和二路备选"
            ),
            ModelOption(
                id="mimo_v2_5_pro", name="MiMo V2.5 Pro",
                provider="xiaomi", api_base="https://api.xiaomimimo.com",
                model_name="mimo-v2.5-pro", api_key_env="MIMO_API_KEY",
                cost_per_m_tokens=0, max_context=1_000_000,
                channel="official", modalities=["text", "tool"],
                quality_tier="high", cost_tier="normal",
                notes="长上下文整理、脚本二审、中文质量校验"
            ),
            ModelOption(
                id="glm_5_1_relay", name="GLM-5.1 Relay",
                provider="zhipu_relay", api_base="${GLM_RELAY_BASE_URL}",
                model_name="glm-5.1", api_key_env="GLM_RELAY_API_KEY",
                cost_per_m_tokens=0, max_context=0,
                channel="new_api_relay", modalities=["text", "tool"],
                quality_tier="flagship", cost_tier="normal",
                api_compatibility="openai_chat", supports_json=True, supports_tools=True,
                fallback_ids=["gpt_5_5_relay", "deepseek_v4pro"],
                notes="深度推理第一顺位：策略、脚本诊断、方案评审、复杂归因"
            ),
            ModelOption(
                id="gpt_5_5_relay", name="GPT-5.5 Relay",
                provider="openai_relay", api_base="${OPENAI_RELAY_BASE_URL}",
                model_name="gpt-5.5", api_key_env="OPENAI_RELAY_API_KEY",
                cost_per_m_tokens=216, max_context=128_000,
                channel="new_api_relay", modalities=["text", "image"],
                quality_tier="flagship", cost_tier="high",
                api_compatibility="openai_chat",
                fallback_ids=["deepseek_v4pro"],
                notes="深度推理第二顺位；记录中转通道稳定性、计费和工具调用差异"
            ),
        ]
    ),

    "multimodal": FunctionSlot(
        function_id="multimodal",
        function_name="多模态理解（图文/视频分析）",
        active_id="mimo_omni",
        options=[
            ModelOption(
                id="mimo_omni", name="MiMo V2 Omni",
                provider="xiaomi", api_base="https://api.xiaomimimo.com",
                model_name="mimo-v2-omni", api_key_env="MIMO_API_KEY",
                notes="音频/图像/视频理解主线候选"
            ),
            ModelOption(
                id="minimax_m2_7", name="MiniMax M2.7",
                provider="minimax", api_base="https://api.minimax.io/v1",
                model_name="M2.7", api_key_env="MINIMAX_API_KEY",
                quality_tier="normal", cost_tier="normal",
                notes="已购基线/最后兜底；不进入默认主链路，除非样例盲测胜出"
            ),
            ModelOption(
                id="gpt_vision_relay", name="GPT Vision Relay",
                provider="openai_relay", api_base="${OPENAI_RELAY_BASE_URL}",
                model_name="gpt-5.5", api_key_env="OPENAI_RELAY_API_KEY",
                channel="new_api_relay", modalities=["text", "image"],
                quality_tier="flagship", cost_tier="high",
                api_compatibility="openai_chat",
                notes="视觉评审候选；记录中转通道稳定性和图片输入能力差异"
            ),
        ]
    ),

    "image_gen": FunctionSlot(
        function_id="image_gen",
        function_name="图像生成（封面/场景/分镜参考图）",
        active_id="gpt_image2_relay",
        options=[
            ModelOption(
                id="gpt_image2_relay", name="GPT-Image-2 Relay",
                provider="openai_relay", api_base="${OPENAI_RELAY_BASE_URL}",
                model_name="gpt-image-2", api_key_env="OPENAI_RELAY_API_KEY",
                channel="new_api_relay", modalities=["image"],
                quality_tier="flagship", cost_tier="high",
                api_compatibility="openai_responses",
                supports_image_edit=True, supports_reference_image=True,
                supports_9_16=True,
                fallback_ids=["firefly_image", "imagen_4", "seedream", "flux", "minimax_image_01"],
                notes="图像生产主线：封面、分镜参考、缺失素材补图；按中转通道记录失败率和成本"
            ),
            ModelOption(
                id="firefly_image", name="Adobe Firefly",
                provider="adobe", api_base="https://firefly-api.adobe.io",
                model_name="firefly-image", api_key_env="FIREFLY_API_KEY",
                channel="official", modalities=["image"],
                quality_tier="high", cost_tier="normal",
                supports_reference_image=True,
                notes="图像外部横评候选，重点关注商用授权、版权安全和设计一致性"
            ),
            ModelOption(
                id="imagen_4", name="Google Imagen",
                provider="google", api_base="https://aiplatform.googleapis.com",
                model_name="imagen", api_key_env="GOOGLE_CLOUD_PROJECT",
                channel="official", modalities=["image"],
                quality_tier="high", cost_tier="normal",
                supports_reference_image=True,
                notes="图像外部横评候选，适合真实感、场景补图和高质量参考图"
            ),
            ModelOption(
                id="seedream", name="Seedream",
                provider="bytedance", api_base="https://ark.cn-beijing.volces.com",
                model_name="seedream", api_key_env="SEEDREAM_API_KEY",
                channel="official", modalities=["image"],
                quality_tier="high", cost_tier="normal",
                supports_reference_image=True,
                notes="中文场景图像横评候选，需确认当前API权限和商用条款"
            ),
            ModelOption(
                id="flux", name="FLUX",
                provider="black_forest_labs", api_base="https://api.bfl.ai",
                model_name="flux", api_key_env="FLUX_API_KEY",
                channel="official", modalities=["image"],
                quality_tier="high", cost_tier="normal",
                supports_reference_image=True,
                notes="图像外部横评候选，适合风格和细节质量对比"
            ),
            ModelOption(
                id="minimax_image_01", name="MiniMax image-01",
                provider="minimax", api_base="https://api.minimax.io/v1",
                model_name="image-01", api_key_env="MINIMAX_API_KEY",
                channel="official", modalities=["image"],
                quality_tier="normal", cost_tier="normal",
                supports_reference_image=True, supports_9_16=True,
                notes="已购图像最后兜底：中转和外部候选不可用、批量低风险参考图或样例盲测胜出时使用"
            ),
            ModelOption(
                id="dreamina", name="Dreamina (即梦)",
                provider="bytedance", api_base="https://api.dreamina.com",
                model_name="dreamina-v2", api_key_env="DREAMINA_API_KEY",
                notes="后续备选，暂不购买"
            ),
        ]
    ),

    "video_gen": FunctionSlot(
        function_id="video_gen",
        function_name="视频生成（空镜/B-roll片段）",
        active_id="runway_gen4_turbo",
        options=[
            ModelOption(
                id="runway_gen4_turbo", name="Runway Gen-4 Turbo",
                provider="runway", api_base="https://api.dev.runwayml.com",
                model_name="gen4_turbo", api_key_env="RUNWAY_API_KEY",
                channel="official", modalities=["video"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="async_task", supports_reference_image=True,
                supports_9_16=True,
                fallback_ids=["veo_3_1_lite", "veo_3_1_fast", "kling", "luma_ray", "pika", "hailuo_2_3"],
                notes="视频B-roll第一横评和默认候选；按官方credits/sec价格、小额跑30条样例"
            ),
            ModelOption(
                id="veo_3_1_lite", name="Google Veo 3.1 Lite",
                provider="google", api_base="https://aiplatform.googleapis.com",
                model_name="veo-3.1-lite", api_key_env="GOOGLE_CLOUD_PROJECT",
                channel="official", modalities=["video"],
                quality_tier="high", cost_tier="high",
                api_compatibility="async_task", supports_9_16=True,
                fallback_ids=["runway_gen4_turbo", "kling"],
                notes="重点镜头候选；成本高于日更常规B-roll，按镜头价值启用"
            ),
            ModelOption(
                id="veo_3_1_fast", name="Google Veo 3.1 Fast/Lite",
                provider="google", api_base="https://aiplatform.googleapis.com",
                model_name="veo-3.1-fast", api_key_env="GOOGLE_CLOUD_PROJECT",
                channel="official", modalities=["video"],
                quality_tier="flagship", cost_tier="high",
                api_compatibility="async_task", supports_9_16=True,
                notes="高真实运动和重点镜头候选，成本高，不作为日更主线"
            ),
            ModelOption(
                id="kling", name="可灵AI",
                provider="kuaishou",
                api_base="https://api-singapore.klingai.com",
                model_name="", api_key_env="KLING_ACCESS_KEY",
                channel="official", modalities=["video"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="async_task", supports_reference_image=True,
                supports_9_16=True,
                notes="中文短视频生态候选；API、价格和地区限制需实测"
            ),
            ModelOption(
                id="luma_ray", name="Luma Ray",
                provider="luma", api_base="https://api.lumalabs.ai",
                model_name="ray", api_key_env="LUMA_API_KEY",
                channel="official", modalities=["video"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="async_task", supports_reference_image=True,
                supports_9_16=True,
                notes="风格化和运动镜头候选，按镜头需求小额测试"
            ),
            ModelOption(
                id="pika", name="Pika",
                provider="pika", api_base="https://api.pika.art",
                model_name="pika", api_key_env="PIKA_API_KEY",
                channel="official", modalities=["video"],
                quality_tier="normal", cost_tier="normal",
                api_compatibility="async_task", supports_reference_image=True,
                notes="风格化短视频候选；API权限、价格和商用条款需购买前确认"
            ),
            ModelOption(
                id="hailuo_2_3", name="MiniMax Hailuo-2.3 768P 6s",
                provider="minimax", api_base="https://api.minimax.io/v1",
                model_name="Hailuo-2.3-768P-6s", api_key_env="MINIMAX_API_KEY",
                channel="official", modalities=["video"],
                quality_tier="normal", cost_tier="normal",
                api_compatibility="async_task", supports_9_16=True,
                fallback_ids=["hailuo_2_3_fast"],
                notes="已购视频最后兜底/基线；不作为默认主链路，除非样例盲测胜出"
            ),
            ModelOption(
                id="hailuo_2_3_fast", name="MiniMax Hailuo-2.3-Fast 768P 6s",
                provider="minimax", api_base="https://api.minimax.io/v1",
                model_name="Hailuo-2.3-Fast-768P-6s", api_key_env="MINIMAX_API_KEY",
                channel="official", modalities=["video"],
                quality_tier="normal", cost_tier="low",
                api_compatibility="async_task", supports_9_16=True,
                notes="已购低成本基线/最后兜底，用于和外部模型同题比较"
            ),
        ]
    ),

    "voice_clone": FunctionSlot(
        function_id="voice_clone",
        function_name="方言语音克隆（配音生成）",
        active_id="mimo_voiceclone",
        options=[
            ModelOption(
                id="mimo_voiceclone", name="MiMo V2.5 TTS VoiceClone",
                provider="xiaomi", api_base="https://api.xiaomimimo.com",
                model_name="mimo-v2.5-tts-voiceclone", api_key_env="MIMO_API_KEY",
                channel="official", modalities=["audio"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="native",
                fallback_ids=["mimo_voicedesign", "mimo_tts", "elevenlabs_tts", "cartesia_tts", "openai_tts", "minimax_speech"],
                notes="语音主线，优先评估攸县方言咬字、音色相似度和情绪稳定性"
            ),
            ModelOption(
                id="mimo_tts", name="MiMo V2.5 TTS",
                provider="xiaomi", api_base="https://api.xiaomimimo.com",
                model_name="mimo-v2.5-tts", api_key_env="MIMO_API_KEY",
                channel="official", modalities=["audio"],
                quality_tier="normal", cost_tier="low",
                api_compatibility="native",
                fallback_ids=["openai_tts", "elevenlabs_tts", "minimax_speech"],
                notes="草稿配音、普通旁白和低成本版本"
            ),
            ModelOption(
                id="mimo_voicedesign", name="MiMo V2.5 TTS VoiceDesign",
                provider="xiaomi", api_base="https://api.xiaomimimo.com",
                model_name="mimo-v2.5-tts-voicedesign", api_key_env="MIMO_API_KEY",
                channel="official", modalities=["audio"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="native",
                notes="角色声线与非本人克隆声线"
            ),
            ModelOption(
                id="elevenlabs_tts", name="ElevenLabs TTS/Voice",
                provider="elevenlabs", api_base="https://api.elevenlabs.io",
                model_name="eleven_multilingual", api_key_env="ELEVENLABS_API_KEY",
                channel="official", modalities=["audio"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="native",
                fallback_ids=["cartesia_tts", "openai_tts", "minimax_speech"],
                notes="外部高质量语音第一横评候选；重点测试中文情绪、方言咬字和声音克隆效果"
            ),
            ModelOption(
                id="cartesia_tts", name="Cartesia Sonic",
                provider="cartesia", api_base="https://api.cartesia.ai",
                model_name="sonic", api_key_env="CARTESIA_API_KEY",
                channel="official", modalities=["audio"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="native",
                fallback_ids=["openai_tts", "minimax_speech"],
                notes="外部语音第二横评候选；低延迟强，后续互动语音Agent优先级更高"
            ),
            ModelOption(
                id="openai_tts", name="OpenAI TTS",
                provider="openai", api_base="${OPENAI_RELAY_BASE_URL}",
                model_name="tts", api_key_env="OPENAI_TTS_API_KEY",
                channel="official_or_relay", modalities=["audio"],
                quality_tier="normal", cost_tier="normal",
                api_compatibility="openai_responses",
                fallback_ids=["minimax_speech"],
                notes="普通旁白和标准中文稳定兜底；不作为方言克隆主线"
            ),
            ModelOption(
                id="minimax_speech", name="MiniMax Speech 2.8",
                provider="minimax", api_base="https://api.minimax.io/v1",
                model_name="Speech-2.8", api_key_env="MINIMAX_API_KEY",
                cost_per_m_tokens=0,
                channel="official", modalities=["audio"],
                quality_tier="normal", cost_tier="normal",
                api_compatibility="native",
                notes="已购语音最后兜底/基线；仅小米和外部候选不可用、成本异常或盲测胜出时切换"
            ),
        ]
    ),

    "digital_human": FunctionSlot(
        function_id="digital_human",
        function_name="AI数字人（口播视频）",
        active_id="heygen",
        options=[
            ModelOption(
                id="heygen", name="HeyGen Avatar API",
                provider="heygen", api_base="https://api.heygen.com",
                model_name="", api_key_env="HEYGEN_API_KEY",
                cost_per_m_tokens=0,
                channel="official", modalities=["avatar", "video"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="async_task", supports_9_16=True,
                fallback_ids=["tavus", "d_id", "akool"],
                notes="数字人口播主线；启动前确认API权限、Avatar类型、9:16、并发和每分钟成本"
            ),
            ModelOption(
                id="tavus", name="Tavus",
                provider="tavus", api_base="https://tavusapi.com",
                model_name="", api_key_env="TAVUS_API_KEY",
                channel="official", modalities=["avatar", "video"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="async_task",
                supports_9_16=True,
                notes="数字人第二候选，适合API化、Replica和后续互动数字人"
            ),
            ModelOption(
                id="d_id", name="D-ID Talking Avatar",
                provider="d_id", api_base="https://api.d-id.com",
                model_name="", api_key_env="D_ID_API_KEY",
                channel="official", modalities=["avatar", "video"],
                quality_tier="normal", cost_tier="normal",
                api_compatibility="async_task",
                notes="单图说话和低成本口播兜底"
            ),
            ModelOption(
                id="akool", name="AKOOL Talking Avatar",
                provider="akool", api_base="https://openapi.akool.com",
                model_name="", api_key_env="AKOOL_API_KEY",
                channel="official", modalities=["avatar", "video"],
                quality_tier="normal", cost_tier="normal",
                api_compatibility="async_task",
                supports_9_16=True,
                notes="营销素材和低成本口播横评候选"
            ),
        ]
    ),
}


class ModelRegistry:
    """模型注册中心 — 读取/切换/编辑参数/持久化

    持久化文件 data/model_state.json 结构：
    {
      "text_llm": {
        "active_id": "deepseek_v4pro",
        "overrides": {
          "deepseek_v4pro": {
            "api_base": "https://api.deepseek.com",   // 用户自定义覆盖
            "api_key": "sk-xxx...",                      // 直接存储的密钥（加密）
            "model_name": "deepseek-v4-pro"              // 用户自定义覆盖
          }
        }
      },
      ...
    }
    """

    STATE_FILE = "data/model_state.json"

    @classmethod
    def get_active(cls, function_id: str) -> ModelOption:
        """获取某功能维度的当前激活模型（含用户自定义参数覆盖）"""
        slot = REGISTRY[function_id]
        state = cls._load_state()
        func_state = state.get(function_id, {})
        active_id = func_state.get("active_id", slot.active_id)

        # 找到基础模型定义，深拷贝避免污染全局注册表
        base = copy.deepcopy(next((o for o in slot.options if o.id == active_id), slot.options[0]))

        # 应用用户自定义覆盖（优先使用用户在Web界面设置的值）
        overrides = func_state.get("overrides", {}).get(active_id, {})
        if overrides.get("api_base"):
            base.api_base = overrides["api_base"]
        if overrides.get("model_name"):
            base.model_name = overrides["model_name"]
        # API Key优先级：用户直接填写的 > .env环境变量
        if overrides.get("api_key"):
            base.resolved_api_key = overrides["api_key"]
        else:
            base.resolved_api_key = os.environ.get(base.api_key_env, "")

        return base

    @classmethod
    def snapshot(cls, function_id: str) -> ModelOption:
        """任务启动时快照当前模型配置，运行期间不受切换影响"""
        return cls.get_active(function_id)

    @classmethod
    def switch(cls, function_id: str, model_id: str):
        """切换模型（Web后台调用，立即生效）"""
        slot = REGISTRY[function_id]
        valid = any(o.id == model_id for o in slot.options)
        if not valid:
            raise ValueError(f"模型 {model_id} 不在 {function_id} 的可用列表中")
        state = cls._load_state()
        if function_id not in state:
            state[function_id] = {}
        state[function_id]["active_id"] = model_id
        cls._save_state(state)

    @classmethod
    def update_model_config(cls, function_id: str, model_id: str,
                            api_base: str = None, api_key: str = None,
                            model_name: str = None):
        """更新某个模型的自定义参数（Web后台编辑API URL/Key等）"""
        state = cls._load_state()
        if function_id not in state:
            state[function_id] = {"active_id": "", "overrides": {}}
        if "overrides" not in state[function_id]:
            state[function_id]["overrides"] = {}
        if model_id not in state[function_id]["overrides"]:
            state[function_id]["overrides"][model_id] = {}

        overrides = state[function_id]["overrides"][model_id]
        if api_base is not None:
            overrides["api_base"] = api_base
        if api_key is not None:
            overrides["api_key"] = _encrypt(api_key)  # 加密存储
        if model_name is not None:
            overrides["model_name"] = model_name

        cls._save_state(state)

    @classmethod
    def get_model_config(cls, function_id: str, model_id: str) -> dict:
        """获取某个模型的当前配置（含覆盖值，API Key脱敏显示）"""
        slot = REGISTRY[function_id]
        base = next((o for o in slot.options if o.id == model_id), None)
        if not base:
            return {}

        state = cls._load_state()
        overrides = state.get(function_id, {}).get("overrides", {}).get(model_id, {})

        # 解密API Key用于回显（脱敏）
        stored_key = overrides.get("api_key", "")
        decrypted_key = _decrypt(stored_key) if stored_key else ""

        return {
            "id": base.id,
            "name": base.name,
            "provider": base.provider,
            "api_base": overrides.get("api_base", base.api_base),
            "model_name": overrides.get("model_name", base.model_name),
            "api_key_env": base.api_key_env,
            "api_key_masked": _mask(decrypted_key) if decrypted_key else "（未设置，将从.env读取）",
            "has_custom_key": bool(decrypted_key),
            "cost_per_m_tokens": base.cost_per_m_tokens,
            "max_context": base.max_context,
            "notes": base.notes,
        }

    @classmethod
    def list_all(cls) -> dict:
        """列出所有功能维度的可选模型和当前激活状态（含配置信息）"""
        state = cls._load_state()
        result = {}
        for fid, slot in REGISTRY.items():
            func_state = state.get(fid, {})
            active_id = func_state.get("active_id", slot.active_id)
            result[fid] = {
                "function_name": slot.function_name,
                "active_id": active_id,
                "active_name": next(
                    (o.name for o in slot.options if o.id == active_id),
                    slot.options[0].name
                ),
                "options": [
                    cls.get_model_config(fid, o.id)
                    for o in slot.options
                ]
            }
        return result

    @classmethod
    def _load_state(cls) -> dict:
        path = Path(cls.STATE_FILE)
        if path.exists():
            return json.loads(path.read_text())
        return {}

    @classmethod
    def _save_state(cls, state: dict):
        path = Path(cls.STATE_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        # 备份旧文件
        if path.exists():
            bak = path.with_suffix(".bak")
            if bak.exists():
                bak.unlink()
            path.rename(bak)
        # 原子写入：先写临时文件，再替换
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        os.replace(str(tmp), str(path))


# ─── API Key 加密/解密/脱敏 工具函数 ───

from cryptography.fernet import Fernet

def _get_cipher() -> Fernet:
    """从环境变量派生加密密钥"""
    key_material = os.environ.get("MASTER_ENCRYPTION_KEY", "") + os.environ.get("HOSTNAME", "local")
    key = hashlib.sha256(key_material.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))

def _encrypt(plain: str) -> str:
    """加密API Key"""
    if not plain:
        return ""
    return _get_cipher().encrypt(plain.encode()).decode()

def _decrypt(cipher: str) -> str:
    """解密API Key"""
    if not cipher:
        return ""
    return _get_cipher().decrypt(cipher.encode()).decode()

def _mask(key: str) -> str:
    """脱敏显示API Key（仅保留前4后4位）"""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]
```

### 4.3 Service层对接（统一调用入口）

每个service通过Registry获取当前激活模型，无需硬编码：

```python
# services/llm.py（改造后）

import json
import os
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config.model_registry import ModelRegistry

class LLMAbstract:
    """LLM统一调用层 — 自动路由到当前激活模型"""

    def __init__(self, function_id: str = "text_llm"):
        self.function_id = function_id

    def _get_client(self):
        """根据当前激活模型，返回对应的异步API client和模型名"""
        model = ModelRegistry.snapshot(self.function_id)
        api_key = model.resolved_api_key  # get_active()中已统一解析，无需二次fallback

        if model.provider in ("deepseek", "openai", "zhipu", "openai_relay", "anthropic_relay", "zhipu_relay"):
            # OpenAI兼容格式（DeepSeek、GLM与New API中转都走统一客户端）
            return AsyncOpenAI(
                api_key=api_key,
                base_url=model.api_base
            ), model.model_name

        elif model.provider == "minimax":
            return MiniMaxClient(
                api_key=api_key,
                base_url=model.api_base
            ), model.model_name

        elif model.provider == "bytedance":
            return ByteDanceClient(
                api_key=api_key,
                base_url=model.api_base
            ), model.model_name

        raise ValueError(f"不支持的provider: {model.provider}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    async def chat(self, messages: list, **kwargs) -> str:
        """通用聊天接口，自动路由，含重试"""
        client, model_name = self._get_client()
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

    async def chat_json(self, messages: list, **kwargs) -> dict:
        """JSON格式输出"""
        content = await self.chat(messages, response_format={"type": "json_object"}, **kwargs)
        return json.loads(content)

# 全局实例（各Agent直接import使用）
text_llm = LLMAbstract("text_llm")
multimodal_llm = LLMAbstract("multimodal")
```

```python
# services/voice.py（改造后 — 策略模式 + 共享httpx客户端）

import httpx
from pathlib import Path
from config.model_registry import ModelRegistry

# ─── 共享httpx.AsyncClient复用 ───

_shared_client: httpx.AsyncClient | None = None

async def get_http_client() -> httpx.AsyncClient:
    """获取共享的httpx异步客户端，避免反复创建/销毁连接"""
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _shared_client

# ─── 各语音供应商的具体实现 ───

async def _minimax_tts(text, path, model):
    """MiniMax Speech 2.8 API调用（最后兜底/基线方案）"""
    c = await get_http_client()
    resp = await c.post(f"{model.api_base}/t2a_v2", json={
        "model": "Speech-2.8",
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": "yuxian_dialect_clone",
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 24000,
            "format": "wav",
        },
    }, headers={
        "Authorization": f"Bearer {model.resolved_api_key}",
    })
    Path(path).write_bytes(resp.content)
    return path

async def _mimo_tts(text, path, model):
    """MiMo TTS / VoiceClone / VoiceDesign API调用（语音主线）"""
    c = await get_http_client()
    resp = await c.post(
        f"{model.api_base}/v1/audio/speech",
        json={
            "model": model.model_name,
            "text": text,
            "voice_id": "yuxian_dialect_clone",
            "format": "wav",
        },
        headers={"Authorization": f"Bearer {model.resolved_api_key}"},
        timeout=60,
    )
    Path(path).write_bytes(resp.content)
    return path

async def _external_tts(text, path, model):
    """ElevenLabs / Cartesia 等外部语音横评候选"""
    c = await get_http_client()
    resp = await c.post(
        f"{model.api_base}/tts",
        json={"text": text, "model": model.model_name},
        headers={"Authorization": f"Bearer {model.resolved_api_key}"},
        timeout=60,
    )
    Path(path).write_bytes(resp.content)
    return path

# ─── 策略分发字典（替代if-elif链） ───

VOICE_PROVIDERS = {
    "mimo_voiceclone": _mimo_tts,
    "mimo_tts": _mimo_tts,
    "mimo_voicedesign": _mimo_tts,
    "minimax_speech": _minimax_tts,
    "elevenlabs": _external_tts,
    "cartesia": _external_tts,
}

async def generate_voice(text: str, output_path: str) -> str:
    """根据当前激活模型自动路由到对应语音供应商"""
    model = ModelRegistry.snapshot("voice_clone")
    provider_fn = VOICE_PROVIDERS.get(model.id)
    if not provider_fn:
        raise ValueError(f"不支持的语音模型: {model.id}")
    return await provider_fn(text, output_path, model)
```

其他service（digital_human.py, video_gen.py, image_gen.py）同理改造。

### 4.4 Web后台设置页

```python
# web/pages/settings.py（Streamlit页面）

import streamlit as st
from config.model_registry import ModelRegistry

def render_settings_page():
    st.title("模型设置")
    st.markdown("选择各功能维度的模型，并可自定义API地址、密钥、模型名称等参数。")

    registry_data = ModelRegistry.list_all()

    for fid, info in registry_data.items():
        with st.expander(f"{'✅' if True else '🔹'} {info['function_name']}", expanded=True):
            # ── 模型选择 ──
            options = info["options"]
            active_id = info["active_id"]
            option_labels = []
            for o in options:
                tag = " ⭐" if o["id"] == active_id else ""
                option_labels.append(f"{o['name']}{tag}")

            current_idx = next(
                i for i, o in enumerate(options) if o["id"] == active_id
            )

            selected_label = st.radio(
                label="选择模型",
                options=option_labels,
                index=current_idx,
                key=f"model_{fid}",
                horizontal=True
            )

            sel_idx = option_labels.index(selected_label)
            sel_model = options[sel_idx]

            # ── 模型说明 ──
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.caption(f"💡 {sel_model['notes']}")
            with col_info2:
                if sel_model["cost_per_m_tokens"] > 0:
                    st.caption(f"💰 成本：¥{sel_model['cost_per_m_tokens']}/百万tokens")
                st.caption(f"📐 上下文：{sel_model['max_context']:,} tokens" if sel_model['max_context'] else "")

            # ── API参数编辑区 ──
            st.markdown("---")
            st.markdown("**API 参数配置**")

            api_base_val = st.text_input(
                "API 地址 (Base URL)",
                value=sel_model["api_base"],
                key=f"api_base_{fid}_{sel_model['id']}",
                help="模型的API端点地址，可替换为自部署地址"
            )

            model_name_val = st.text_input(
                "模型名称 (Model Name)",
                value=sel_model["model_name"],
                key=f"model_name_{fid}_{sel_model['id']}",
                help="API调用时使用的模型标识"
            )

            # API Key输入（显示脱敏值，支持重新输入）
            key_hint = sel_model["api_key_masked"]
            api_key_input = st.text_input(
                "API Key",
                value="",
                placeholder=key_hint,
                type="password",
                key=f"api_key_{fid}_{sel_model['id']}",
                help=f"直接填入API Key。留空则从环境变量 {sel_model['api_key_env']} 读取"
            )

            # ── 操作按钮 ──
            col_save, col_switch = st.columns(2)

            with col_save:
                if st.button("💾 保存参数", key=f"save_{fid}"):
                    ModelRegistry.update_model_config(
                        function_id=fid,
                        model_id=sel_model["id"],
                        api_base=api_base_val if api_base_val != sel_model["api_base"] else None,
                        model_name=model_name_val if model_name_val != sel_model["model_name"] else None,
                        api_key=api_key_input if api_key_input else None,
                    )
                    st.success(f"已保存 {sel_model['name']} 的参数配置")
                    st.rerun()

            with col_switch:
                if sel_model["id"] != active_id:
                    if st.button(f"🔄 切换到 {sel_model['name']}", key=f"switch_{fid}"):
                        # 先保存参数，再切换
                        ModelRegistry.update_model_config(
                            function_id=fid,
                            model_id=sel_model["id"],
                            api_base=api_base_val if api_base_val != sel_model["api_base"] else None,
                            model_name=model_name_val if model_name_val != sel_model["model_name"] else None,
                            api_key=api_key_input if api_key_input else None,
                        )
                        ModelRegistry.switch(fid, sel_model["id"])
                        st.success(f"已切换到 {sel_model['name']} 并保存参数")
                        st.rerun()
                else:
                    st.info("当前正在使用此模型")

            # ── 连通性测试 ──
            if st.button("🔍 测试连接", key=f"test_{fid}"):
                with st.spinner("正在测试API连通性..."):
                    result = test_api_connection(
                        api_base=api_base_val,
                        model_name=model_name_val,
                        api_key=api_key_input or None,
                        env_key=sel_model["api_key_env"],
                        provider=sel_model["provider"],
                    )
                    if result["ok"]:
                        st.success(f"✅ 连接成功！模型响应正常（延迟 {result['latency_ms']}ms）")
                    else:
                        st.error(f"❌ 连接失败：{result['error']}")
```

**页面效果：**

```
┌─────────────────────────────────────────────┐
│  模型设置                                    │
├─────────────────────────────────────────────┤
│                                             │
│  文本LLM（选题/脚本/分镜/分析）               │
│  ● DeepSeek V4 Flash(日常)  ○ GLM-5.1(深度)  ○ GPT-5.5/DeepSeek Pro │
│  💡 Flash批量生成，深度推理按GLM→GPT→DeepSeek路由 │
│  [切换]                                     │
│                                             │
│  多模态理解（图文/视频分析）                   │
│  ● MiMo Omni  ○ GPT/Claude Relay  ○ MiniMax M2.7基线 │
│  💡 MiniMax仅做基线，中转模型记录稳定性和API差异 │
│  [切换]                                     │
│                                             │
│  图像生成（封面/场景/分镜参考图）              │
│  ● GPT-Image-2 Relay  ○ Firefly/Imagen/Seedream  ○ image-01兜底 │
│  💡 GPT-image-2生产主线，MiniMax image-01最后兜底 │
│  [切换]                                     │
│                                             │
│  视频生成（空镜/B-roll片段）                  │
│  ● Runway Gen-4 Turbo  ○ Veo/Kling/Luma/Pika  ○ Hailuo基线兜底 │
│  💡 外部视频先小额横评，Hailuo不再做默认主线 │
│  [切换]                                     │
│                                             │
│  方言语音克隆（配音生成）                      │
│  ● MiMo VoiceClone  ○ ElevenLabs/Cartesia/OpenAI  ○ MiniMax兜底 │
│  💡 小米语音优先，外部语音小额横评，MiniMax最后兜底 │
│  [切换]                                     │
│                                             │
│  AI数字人（口播视频）                         │
│  ● HeyGen  ○ Tavus  ○ D-ID/AKOOL             │
│  💡 按口型质量、分钟成本、API权限和竖屏适配决策 │
│  [切换]                                     │
└─────────────────────────────────────────────┘
```

### 4.4.1 设置页状态管理优化

为避免 Streamlit rerun 时表单数据丢失，每个功能维度的编辑区域使用 `st.form` 包裹，实现批量提交：

```python
# web/pages/settings.py — 设置页优化：使用 st.form 批量提交

# 在 render_settings_page() 中，每个功能维度的 API 参数编辑区替换为：

with st.form(f"form_{fid}"):
    api_base_val = st.text_input("API 地址", value=sel_model["api_base"], key=f"ab_{fid}")
    model_name_val = st.text_input("模型名称", value=sel_model["model_name"], key=f"mn_{fid}")
    api_key_input = st.text_input(
        "API Key", type="password",
        placeholder=sel_model["api_key_masked"], key=f"ak_{fid}"
    )

    col1, col2 = st.columns(2)
    with col1:
        submitted = st.form_submit_button("💾 保存参数")
    with col2:
        switch_submitted = st.form_submit_button(f"🔄 切换到 {sel_model['name']}")

    if submitted:
        ModelRegistry.update_model_config(
            function_id=fid,
            model_id=sel_model["id"],
            api_base=api_base_val if api_base_val != sel_model["api_base"] else None,
            model_name=model_name_val if model_name_val != sel_model["model_name"] else None,
            api_key=api_key_input if api_key_input else None,
        )
        st.toast(f"已保存 {sel_model['name']} 的参数")  # 用toast替代rerun

    if switch_submitted:
        ModelRegistry.update_model_config(
            function_id=fid,
            model_id=sel_model["id"],
            api_base=api_base_val if api_base_val != sel_model["api_base"] else None,
            model_name=model_name_val if model_name_val != sel_model["model_name"] else None,
            api_key=api_key_input if api_key_input else None,
        )
        ModelRegistry.switch(fid, sel_model["id"])
        st.toast(f"已切换到 {sel_model['name']} 并保存参数")  # 用toast替代rerun
```

**优化要点：**
- 使用 `st.form` 包裹每个功能维度的编辑区域，用户在提交前可自由修改多个字段
- 提交后使用 `st.toast` 显示反馈，避免 `st.rerun()` 导致其他表单区域的数据丢失
- 只有在需要刷新模型列表时才触发 rerun

### 4.5 切换与参数配置生效机制

```
Web后台操作（3种动作）：
  ├── ① 切换模型 → ModelRegistry.switch() → 写入 active_id
  ├── ② 编辑参数 → ModelRegistry.update_model_config() → 写入 overrides（api_base/api_key/model_name）
  └── ③ 测试连接 → test_api_connection() → 实际调用验证

持久化到 data/model_state.json：
{
  "text_llm": {
    "active_id": "deepseek_v4pro",
    "overrides": {
      "deepseek_v4pro": {
        "api_base": "https://api.deepseek.com",  ← 用户自定义
        "api_key": "enc:xxxx",                    ← 加密存储
        "model_name": "deepseek-v4-pro"           ← 用户自定义
      },
      "glm_5_1": {
        "api_key": "enc:yyyy"                     ← 提前配好，切换即可用
      }
    }
  }
}

Service层调用链：
  ModelRegistry.get_active("text_llm")
    → 读取 active_id → 找到基础 ModelOption
    → 读取 overrides → 覆盖 api_base / model_name
    → 读取 api_key → 优先 overrides 中的密钥，其次 .env 环境变量
    → 返回完整配置的 ModelOption（含 resolved_api_key）
```

- 切换立即生效，无需重启
- 持久化到JSON文件，重启不丢失
- API Key 加密存储（`_encrypt` / `_decrypt`），Web界面脱敏显示
- API Key 优先级：Web界面直接填写 > .env环境变量
- 支持为非激活模型提前配置参数，切换即可用
- 内置连通性测试按钮，验证 API 地址和密钥是否正确

### 4.6 多模型路由与通道策略（新增）

#### 4.6.1 数据结构升级

`ModelOption` 不再用单一信任等级否定中转站模型。模型效果、供应商通道和数据策略分开表达：

```python
@dataclass
class ModelOption:
    id: str
    name: str
    provider: str
    channel: str                  # official / new_api_relay / official_or_relay / local_tool
    modalities: list[str]         # text / image / video / audio / avatar / tool
    api_base: str
    model_name: str
    api_key_env: str
    quality_tier: str = "normal"  # draft / normal / high / flagship
    cost_tier: str = "normal"     # low / normal / high
    latency_tier: str = "normal"  # fast / normal / slow
    data_policy: str = "standard" # public_only / standard / sensitive_allowed / local_only
    api_compatibility: str = ""   # openai_chat / openai_responses / native / async_task
    supports_json: bool = False
    supports_tools: bool = False
    supports_image_edit: bool = False
    supports_reference_image: bool = False
    supports_9_16: bool = False
    fallback_ids: list[str] = field(default_factory=list)
    notes: str = ""
```

通道策略：

| channel | 含义 | 可用范围 | 必须监控 |
|---------|------|----------|----------|
| official | 官方订阅或官方 API | 主链路、生产内容、媒体生成、私有数据按需调用 | 价格、限流、失败率 |
| new_api_relay | New API/OpenAI兼容中转 | 可进入主链路，但要按通道实测 | 上下文、工具调用、图片/文件上传、计费、稳定性 |
| official_or_relay | 既可官方也可中转 | 根据成本/稳定性切换 | 每次调用的实际 channel |
| local_tool | 本地工具、数据库、FFmpeg、规则库 | 本地处理、敏感凭证处理 | 版本、路径、错误日志 |

#### 4.6.2 推荐模型池

```python
DEEP_REASONING = ["glm_5_1_relay", "gpt_5_5_relay", "deepseek_v4pro"]
IMAGE_PRIMARY = ["gpt_image2_relay", "firefly_image", "imagen_4", "seedream", "flux", "minimax_image_01"]
VOICE_PRIMARY = ["mimo_voiceclone", "mimo_voicedesign", "mimo_tts", "elevenlabs_tts", "cartesia_tts", "openai_tts", "minimax_speech"]
VIDEO_PRIMARY = ["runway_gen4_turbo", "veo_3_1_lite", "veo_3_1_fast", "kling", "luma_ray", "pika", "hailuo_2_3", "hailuo_2_3_fast"]
AVATAR_PRIMARY = ["heygen", "tavus", "d_id", "akool"]
```

#### 4.6.3 ModelRouter

```python
class ModelRouter:
    """按任务类型、质量要求和数据策略选择模型"""

    SECRET_TYPES = {"account", "credential", "cookie", "api_key"}

    def select(self, task_type: str, quality: str = "normal",
               data_policy: str = "standard") -> ModelOption:
        if data_policy in self.SECRET_TYPES:
            raise ValueError("账号凭证、Cookie、API Key 不允许传入生成模型")

        if task_type in {"strategy", "architecture_review", "script_diagnosis", "storyboard_json", "weekly_strategy"}:
            return self.first_available(DEEP_REASONING, data_policy)

        if task_type in {"cover", "storyboard_reference", "scene_image"}:
            return self.first_available(IMAGE_PRIMARY, data_policy)

        if task_type in {"voice_clone", "voiceover", "role_voice"}:
            return self.first_available(VOICE_PRIMARY, data_policy)

        if task_type in {"broll", "image_to_video", "text_to_video"}:
            return self.first_available(VIDEO_PRIMARY, data_policy)

        if task_type in {"digital_human", "avatar_video", "lip_sync"}:
            return self.first_available(AVATAR_PRIMARY, data_policy)

        if task_type in {"topic_batch", "title_batch", "tags", "daily_report"}:
            return self.by_id("deepseek_v4_flash")

        return self.by_id("mimo_v2_5")
```

#### 4.6.4 调用日志表

所有模型调用必须写入 `model_call_logs`，用于后续横评和成本归因：

```sql
CREATE TABLE IF NOT EXISTS model_call_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    task_type TEXT NOT NULL,
    model_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    channel TEXT NOT NULL,
    prompt_version TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    cost_estimate REAL DEFAULT 0,
    success INTEGER DEFAULT 0,
    error_message TEXT,
    quality_score REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.6.5 实测横评任务

上线前新增 `scripts/eval_models.py`，用 70 个项目样例跑模型横评：

| 类别 | 样例数 | 候选模型 |
|------|--------|----------|
| 选题创意 | 10 | DeepSeek Flash、MiMo V2.5、GLM-5.1轻量、MiniMax M2.7基线 |
| 深度推理 | 8 | GLM-5.1、GPT-5.5、DeepSeek V4 Pro |
| 方言脚本 | 12 | GLM-5.1、DeepSeek Pro、MiMo Pro、MiniMax M2.7基线 |
| 封面/图像 | 10 | GPT-image-2、Firefly/Imagen/Seedream/FLUX候选、MiniMax image-01兜底 |
| 配音 | 10 | MiMo VoiceClone/TTS/VoiceDesign、ElevenLabs/Cartesia/OpenAI TTS、MiniMax Speech 2.8基线 |
| 视频B-roll | 10 | Runway、Veo、Kling、Luma/Pika候选、Hailuo基线 |
| 数字人 | 6 | HeyGen、Tavus、D-ID、AKOOL、腾讯智影/剪映数字人 |
| 数据分析 | 4 | GLM-5.1、GPT-5.5、DeepSeek Pro |

评分字段：

```text
local_relevance      本地性
dialect_accuracy     方言准确度
hook_strength        开头钩子
structure_quality    结构完整度
production_feasible  可生产性
compliance_risk      合规风险，越低越好
cost_score           成本分
latency_score        延迟分
```

低于 3/5 的模型输出不得进入自动发布链路。

### 4.1 文本LLM API（批量草稿 + 深度推理路由）

```python
# services/llm.py（简单示例，完整版见4.3节LLMAbstract）
from openai import AsyncOpenAI
from config.settings import settings
from services.model_router import ModelRouter

client = AsyncOpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
router = ModelRouter()

async def generate_script(topic: str, dialect_dict: list[str]) -> dict:
    """生成方言视频脚本"""
    model = router.select("script_diagnosis", quality="high")
    response = await client.chat.completions.create(
        model=model.model_name,
        messages=[
            {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
            {"role": "user", "content": f"选题：{topic}\n方言词典：{dialect_dict}"}
        ],
        temperature=0.8,
        max_tokens=4096,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

async def generate_storyboard(script: dict) -> list[dict]:
    """根据脚本生成分镜"""
    model = router.select("storyboard_json", quality="high")
    response = await client.chat.completions.create(
        model=model.model_name,
        messages=[
            {"role": "system", "content": STORYBOARD_SYSTEM_PROMPT},
            {"role": "user", "content": f"脚本：{json.dumps(script, ensure_ascii=False)}"}
        ],
        temperature=0.6,
        max_tokens=4096,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)["shots"]
```

**关键参数：**
- 批量草稿：`deepseek-v4-flash` / `mimo-v2.5` / `glm-5.1`轻量调用；`MiniMax M2.7`仅做基线对照
- 深度推理：`glm-5.1` → `gpt-5.5` → `deepseek-v4-pro`
- 具体端点、上下文和价格从模型注册中心读取，不在业务代码硬编码

### 4.2 MiMo / 外部语音 / MiniMax兜底 API（方言配音）

```python
# services/voice.py（MiMo主线 + ElevenLabs/Cartesia/OpenAI横评 + MiniMax最后兜底示例）
from services.voice import get_http_client

async def generate_voice_mimo(text: str, output_path: str,
                              model_name: str = "mimo-v2.5-tts-voiceclone") -> str:
    """使用MiMo语音模型生成攸县方言口播音频"""
    client = await get_http_client()
    resp = await client.post(
        f"{settings.mimo_base_url}/v1/audio/speech",
        headers={"Authorization": f"Bearer {settings.mimo_api_key}"},
        json={
            "model": model_name,
            "text": text,
            "voice_id": "yuxian_dialect_clone",
            "format": "wav",
        },
        timeout=60
    )
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return output_path
```

实现要求：
- `mimo-v2.5-tts-voiceclone` 为主配音首选。
- `mimo-v2.5-tts-voicedesign` 用于角色声线，不替代本人主声线。
- `mimo-v2.5-tts` 用于低成本草稿旁白。
- `ElevenLabs`、`Cartesia`、`OpenAI TTS` 作为外部小额横评，优先级高于 MiniMax。
- `MiniMax Speech 2.8` 作为已购基线和最后兜底，不做首选。
- 不规划本地训练模型；外部语音 API 在 MiMo 低于 3.5/5、或需要更强情绪/角色声线时小额横评。

### 4.2.1 搭建期 Mock / 本地占位模式（必须实现）

在购买 HeyGen / Runway 前，系统不得因为缺少媒体模型 API Key 而无法跑通。`digital_human.py` 和 `video_gen.py` 必须提供占位模式：

| 模块 | 模式 | 行为 |
|---|---|---|
| 数字人 | `mock` | 使用虚拟本地人设静态图 + 音频 + 字幕生成口播占位视频 |
| 数字人 | `manual` | 输出人工上传所需的音频、文案、头像、参数清单，等待用户从剪映/腾讯智影/HeyGen网页端生成 |
| 数字人 | `heygen` | 采购并配置 API 后，走 HeyGen 自动生成 |
| B-roll | `mock` | 使用 GPT-image-2 参考图做轻微缩放/平移图片动效 |
| B-roll | `local` | 使用本地素材库片段自动裁切和拼接 |
| B-roll | `runway/veo/kling/...` | 采购后调用真实视频模型 |

验收标准：未配置 `HEYGEN_API_KEY` 和 `RUNWAY_API_KEY` 时，仍能完整生成一条可审核的占位成片。
### 4.3 HeyGen API（数字人，采购后启用）

```python
# services/digital_human.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from services.voice import get_http_client  # 共享httpx客户端

HEYGEN_BASE = "https://api.heygen.com"

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
async def create_avatar_video(audio_url: str, avatar_id: str) -> str:
    """生成数字人视频"""
    client = await get_http_client()
    resp = await client.post(
        f"{HEYGEN_BASE}/v2/video/generate",
        headers={
            "X-API-KEY": settings.heygen_api_key,
            "Content-Type": "application/json"
        },
        json={
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "audio",
                    "audio_url": audio_url
                }
            }],
            "dimension": {"width": 1080, "height": 1920}  # 9:16竖版
        },
        timeout=30
    )
    return resp.json()["data"]["video_id"]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
async def check_video_status(video_id: str) -> dict:
    """查询视频生成状态"""
    client = await get_http_client()
    resp = await client.get(
        f"{HEYGEN_BASE}/v1/video_status.get?video_id={video_id}",
        headers={"X-API-KEY": settings.heygen_api_key}
    )
    return resp.json()["data"]
```

### 4.4 Runway/Veo/Kling/Luma/Pika API（视频片段生成，采购后启用）与 Hailuo 兜底

```python
# services/video_gen.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config.settings import settings
from services.voice import get_http_client  # 共享httpx客户端
from services.model_router import ModelRouter

RUNWAY_BASE = "https://api.dev.runwayml.com"
HAILUO_BASE = "https://api.minimax.io/v1"

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
async def text_to_video(prompt: str, duration: str = "5",
                         aspect_ratio: str = "9:16") -> str:
    """文本生成视频：默认通过ModelRouter选择Runway/Veo/Kling/Luma/Pika，Hailuo只做最后兜底"""
    model = ModelRouter().select("text_to_video", quality="high")
    client = await get_http_client()
    if model.id == "runway_gen4_turbo":
        resp = await client.post(
            f"{RUNWAY_BASE}/v1/text_to_video",
            headers={"Authorization": f"Bearer {settings.runway_api_key}"},
            json={"model": "gen4_turbo", "prompt": prompt, "ratio": aspect_ratio, "duration": duration},
            timeout=30
        )
    elif model.id.startswith("hailuo"):
        resp = await client.post(
            f"{HAILUO_BASE}/video_generation",
            headers={"Authorization": f"Bearer {settings.minimax_api_key}", "Content-Type": "application/json"},
            json={"model": "Hailuo-2.3-Fast-768P-6s", "prompt": prompt, "duration": duration,
                  "aspect_ratio": aspect_ratio, "callback_url": f"{WEBHOOK_BASE}/api/webhooks/hailuo"},
            timeout=30
        )
    else:
        resp = await call_native_video_provider(model, prompt, duration, aspect_ratio)
    return resp.json()["task_id"]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
)
async def query_video_task(task_id: str) -> dict:
    """查询视频生成任务"""
    client = await get_http_client()
    resp = await client.get(
        f"{HAILUO_BASE}/video_generation/{task_id}",
        headers={"Authorization": f"Bearer {settings.minimax_api_key}"}
    )
    data = resp.json()
    if data["status"] == "succeed":
        return {
            "status": "done",
            "video_url": data["video_url"]
        }
    return {"status": data["status"]}
```

> 注：各视频模型的精确 endpoint 和字段以当前控制台文档为准；此处表达的是服务层封装结构。默认路由为 Runway Gen-4 Turbo → Veo 3.1 Lite/Fast → Kling → Luma/Pika，Hailuo 仅作为已购基线/最后兜底。

### 4.7 多平台发布

> **重要：易媒无公开API。** 采用「各平台官方API + Playwright自动化」双轨方案。

```python
# services/publisher.py

class MultiPlatformPublisher:
    """多平台发布器"""

    async def publish(self, video_path: str, meta: dict,
                      platforms: list[str]) -> dict:
        results = {}
        for platform in platforms:
            try:
                if platform in OFFICIAL_API_PLATFORMS:
                    results[platform] = await self._publish_via_api(
                        platform, video_path, meta
                    )
                else:
                    results[platform] = await self._publish_via_browser(
                        platform, video_path, meta
                    )
            except Exception as e:
                results[platform] = {"status": "failed", "error": str(e)}
        return results

    async def _publish_via_api(self, platform, video_path, meta):
        """通过平台官方API发布"""
        if platform == "douyin":
            return await self._douyin_api(video_path, meta)
        elif platform == "kuaishou":
            return await self._kuaishou_api(video_path, meta)
        # ...

    async def _publish_via_browser(self, platform, video_path, meta):
        """通过Playwright浏览器自动化发布"""
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            # 使用已保存的cookies登录
            await page.context.add_cookies(
                self._load_cookies(platform)
            )
            # 各平台发布流程
            publisher = BROWSER_FLOWS[platform](page)
            result = await publisher.publish(video_path, meta)
            await browser.close()
            return result

# 平台API优先级
OFFICIAL_API_PLATFORMS = ["douyin", "kuaishou"]
# 需浏览器自动化的平台
BROWSER_PLATFORMS = ["weixin", "xiaohongshu"]
```

**发布方案矩阵：**

| 平台 | 发布方式 | 说明 |
|------|----------|------|
| 抖音 | 官方API | 抖音开放平台，需申请开发者权限 |
| 快手 | 官方API | 快手开放平台 |
| 视频号 | Playwright | 微信视频号API内测中，用浏览器自动化 |
| 小红书 | Playwright | 小红书开放平台权限难申请，用浏览器自动化 |

```python
# services/composer.py
import os
import subprocess
import tempfile
from pathlib import Path
import ffmpeg

def compose_video(
    digital_human_path: str,
    voice_path: str,
    b_roll_clips: list[dict],
    subtitles: list[dict],
    bgm_path: str,
    branding_path: str,
    output_path: str,
    format: str = "9:16"  # "9:16" | "3:4" | "16:9"
) -> str:
    """全自动视频合成，使用tempfile管理临时文件，filter_complex一次性构建处理链"""

    tmp_dir = tempfile.mkdtemp(prefix="youxian_compose_")
    try:
        # 1. 合并数字人视频+方言配音
        base = ffmpeg.input(digital_human_path)
        voice = ffmpeg.input(voice_path)
        merged_path = os.path.join(tmp_dir, "merged.mp4")
        ffmpeg.output(
            base.video, voice.audio,
            merged_path,
            vcodec="copy", acodec="aac"
        ).overwrite_output().run()

        # 2. 构建B-roll overlay处理链（基于merged视频逐步叠加）
        current = ffmpeg.input(merged_path)
        for i, clip in enumerate(b_roll_clips):
            broll = ffmpeg.input(clip["path"])
            scaled = broll.video.filter("scale", clip.get("w", 1080), clip.get("h", 607))
            current = current.overlay(
                scaled,
                x=clip.get("x", 0), y=clip.get("y", 476),
                enable=f"between(t,{clip['start']},{clip['end']})"
            )

        # 3. 烧录字幕（将SRT写入临时文件，挂到filter_complex）
        srt_path = os.path.join(tmp_dir, "subs.srt")
        Path(srt_path).write_text(_generate_srt(subtitles), encoding="utf-8")
        # 字幕滤镜需要转义特殊字符
        srt_safe = srt_path.replace("\\", "/").replace(":", "\\:")
        current = current.video.filter(
            "subtitles", srt_safe,
            force_style="FontName=NotoSansSC,FontSize=20,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&"
        )

        # 4. 混合背景音乐
        bgm = ffmpeg.input(bgm_path).audio.filter("volume", 0.15)
        merged_audio = ffmpeg.input(merged_path).audio
        final_audio = ffmpeg.filter(
            [merged_audio, bgm], "amix",
            inputs=2, duration="first"
        )

        # 5. 根据格式缩放并导出
        scale_map = {"9:16": "1080:1920", "3:4": "1080:1440", "16:9": "1920:1080"}
        vf = f"scale={scale_map.get(format, '1080:1920')}"

        ffmpeg.output(
            current.filter(vf), final_audio,
            output_path,
            vcodec="libx264", acodec="aac",
            preset="medium", crf=23
        ).overwrite_output().run()

        return output_path

    finally:
        # 确保清理所有临时文件
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

def _generate_srt(subtitles: list[dict]) -> str:
    """生成SRT字幕文件"""
    lines = []
    for i, sub in enumerate(subtitles, 1):
        start = _seconds_to_srt_time(sub["start"])
        end = _seconds_to_srt_time(sub["end"])
        text = sub["text"]
        if sub.get("dialect_word"):
            text = f"{text}（{sub['translation']}）"
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)

def export_multi_platform(input_path: str, base_name: str) -> dict:
    """导出多平台版本"""
    outputs = {}
    for fmt in ["9:16", "3:4", "16:9"]:
        out = f"output/final/{base_name}_{fmt.replace(':', 'x')}.mp4"
        compose_video(..., format=fmt, output_path=out)
        outputs[fmt] = out
    return outputs
```

## 五、三个Agent的核心逻辑

### 5.1 内容Agent

```python
# agents/content_agent.py

class ContentAgent:
    """负责：选题共创 → 脚本生成 → 分镜设计"""

    async def run_creative_session(self, user_idea: str) -> list[dict]:
        """Step 1: 用户给出想法，Agent检索+发散创意"""
        # 1. 用DeepSeek检索攸县相关知识
        knowledge = await self.llm.search_knowledge(user_idea)
        # 2. 发散多个角度的选题
        topics = await self.llm.diverge_topics(user_idea, knowledge)
        # 3. 每个选题附带热度预测和预估爆点
        return topics

    async def generate_full_script(self, topic: dict) -> dict:
        """Step 2: 用户选定选题后，自动生成完整脚本"""
        script = await self.llm.generate_script(
            topic=topic["title"],
            dialect_dict=self.load_dialect_dict()
        )
        return script

    async def generate_storyboard(self, script: dict) -> list[dict]:
        """Step 3: 根据脚本生成分镜（含AI参考图）"""
        shots = await self.llm.generate_storyboard(script)
        # 为每个需要参考图的分镜生成图片
        for shot in shots:
            if shot.get("need_reference"):
                shot["reference_image"] = await self.image_gen.generate(
                    shot["visual_description"]
                )
        return shots
```

### 5.2 制作Agent

```python
# agents/production_agent.py
# 注意：所有Agent在任务开始时应使用 ModelRegistry.snapshot() 获取模型配置快照，
# 而非 ModelRegistry.get_active()，确保运行期间不受Web后台切换影响。

class ProductionAgent:
    """负责：配音 → 数字人 → B-roll → 合成 → 多版本导出"""

    async def produce_batch(self, scripts: list[dict]) -> list[str]:
        """批量制作视频"""
        results = []
        for script in scripts:
            video_paths = await self.produce_single(script)
            results.append(video_paths)
        return results

    async def produce_single(self, script: dict) -> dict:
        """制作单条视频（全流程）"""
        # 1. 生成方言配音
        voice_path = await self.voice.generate(
            text=script["full_dialogue"],
            output_path=f"output/voices/{script['id']}.wav"
        )

        # 2. 上传音频到URL（HeyGen需要）
        audio_url = await self._upload_to_storage(voice_path)

        # 3. 生成数字人视频
        video_id = await self.digital_human.create_avatar_video(
            audio_url=audio_url,
            avatar_id=settings.heygen_avatar_id
        )
        # 等待完成（轮询或webhook）
        avatar_video = await self._wait_for_video(video_id)

        # 4. 生成B-roll素材
        b_roll_paths = []
        for shot in script["shots"]:
            if shot["type"] == "b_roll":
                task_id = await self.video_gen.text_to_video(
                    prompt=shot["visual_description"],
                    duration=str(shot["duration"]),
                    aspect_ratio="9:16"
                )
                b_roll = await self._wait_for_kling(task_id)
                b_roll_paths.append({
                    "path": b_roll,
                    "start": shot["start_time"],
                    "end": shot["end_time"]
                })

        # 5. FFmpeg自动合成
        final_paths = self.composer.export_multi_platform(
            digital_human_path=avatar_video,
            voice_path=voice_path,
            b_roll_clips=b_roll_paths,
            subtitles=script["subtitles"],
            bgm_path=self._select_bgm(script["mood"]),
            branding_path="templates/branding/",
            base_name=script["id"]
        )

        return final_paths
```

### 5.3 运营Agent

```python
# agents/ops_agent.py

class OpsAgent:
    """负责：发布调度 + 数据采集 + 分析报告"""

    async def publish_approved(self, video_id: str, platforms: list[str]):
        """发布已审核通过的视频到指定平台"""
        for platform in platforms:
            await self.publisher.publish(
                platform=platform,
                video_path=f"output/final/{video_id}_{PLATFORM_FORMAT[platform]}.mp4",
                title=..., tags=..., description=...
            )

    async def collect_daily_data(self):
        """每日自动采集数据"""
        for platform in ["douyin", "kuaishou", "weixin", "xiaohongshu"]:
            data = await self.analytics.fetch(platform)
            await self.db.save_daily_data(platform, data)

    async def generate_weekly_report(self) -> dict:
        """生成周度分析报告"""
        raw_data = await self.db.get_weekly_data()
        report = await self.llm.analyze_performance(raw_data)
        return report
```

## 六、Web管理后台

### 6.1 技术选型

| 组件 | 选择 | 理由 |
|------|------|------|
| 前端 | Streamlit | Python-only，AI可快速生成，无需前后端分离 |
| 后端 | FastAPI | 轻量、异步、自动生成API文档 |
| 数据库 | SQLite | 单用户场景，零配置 |
| 任务队列 | n8n | 可视化工作流编排，Docker独立部署，支持定时/Webhook触发 |
| 文件存储 | 本地文件系统 | 简单直接 |

### 6.1.1 数据库连接（SQLite WAL模式）

```python
# web/database.py
import sqlite3

def get_connection():
    """获取SQLite连接，启用WAL模式提升并发读写性能"""
    conn = sqlite3.connect("data/youxian.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
```

### 6.1.2 访问控制与认证

Web后台和API接口均需认证，防止未授权访问。

#### Streamlit 登录认证

```python
# web/auth.py — 认证中间件

import streamlit as st
from config.settings import settings

def check_auth():
    """Streamlit 登录认证"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("攸县短视频管理后台")
        password = st.text_input("请输入管理员密码", type="password")
        if st.button("登录"):
            if password == settings.admin_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("密码错误")
        st.stop()
```

#### FastAPI JWT 认证

```python
# web/auth.py — FastAPI JWT 认证（续）

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, settings.admin_password, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
```

#### admin_password 安全配置

`settings.py` 中 `admin_password` 字段无默认值，必须在 `.env` 中设置，启动时校验：

```python
# config/settings.py（admin_password 相关部分）

class Settings(BaseSettings):
    # ...
    admin_password: str  # 无默认值，必须在.env中设置
    # ...

settings = Settings()

# 启动时检查
if settings.admin_password in ("admin", ""):
    raise ValueError("⚠️ 请在.env中设置安全的ADMIN_PASSWORD，不允许使用默认值")
```

#### Streamlit 启动绑定

启动时绑定本地地址，避免外网直接访问：

```bash
streamlit run web/app.py --server.address 127.0.0.1
```

### 6.2 页面功能

**页面1：选题共创 `/create`**
- 用户输入框：提供一个想法/关键词
- "发散创意"按钮 → Agent检索+生成多角度选题
- 展示选题卡片（标题、角度、热度预测、难度）
- 用户选择/修改 → 确认 → 自动进入脚本生成

**页面2：审核中心 `/review`**
- 待审核分镜列表（缩略图+描述）
- 待审核视频列表（内嵌播放器）
- 操作：通过 / 打回（填写修改意见，Agent自动迭代）

**页面3：发布管理 `/publish`**
- 已通过的视频队列
- 选择发布平台和时间
- 一键发布 / 定时发布

**页面4：数据看板 `/dashboard`**
- 各平台粉丝趋势图
- 内容表现TOP榜
- 周度分析报告

### 6.3 审核页结构化修改界面（修改意见映射机制）

审核页提供结构化的修改操作，替代自由文本输入，将修改意见精确映射到回退阶段和具体操作。

#### 6.3.1 审核页界面

```python
# web/pages/review.py — 结构化修改界面

def render_review_page():
    st.title("视频审核")
    pending = get_pending_videos()  # 从数据库获取待审核视频

    for i, video in enumerate(pending):
        st.markdown(f"### 视频 {i+1}/{len(pending)}: {video['title']}")
        st.video(video['video_url'])

        # 快速操作
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ 通过", key=f"pass_{video['id']}"):
                approve_video(video['id'])
        with col2:
            if st.button("🔄 轻微修改", key=f"minor_{video['id']}"):
                st.session_state[f"edit_mode_{video['id']}"] = "minor"
        with col3:
            if st.button("❌ 重新制作", key=f"reject_{video['id']}"):
                st.session_state[f"edit_mode_{video['id']}"] = "major"

        # 结构化修改表单
        edit_mode = st.session_state.get(f"edit_mode_{video['id']}")
        if edit_mode:
            with st.form(f"edit_{video['id']}"):
                if edit_mode == "minor":
                    # 轻微修改：选择修改维度
                    dimensions = st.multiselect("修改维度",
                        ["画面/B-roll", "配音/语气", "字幕/翻译", "背景音乐", "字幕样式"],
                        key=f"dim_{video['id']}")
                    instruction = st.text_area("具体修改要求", key=f"inst_{video['id']}")
                    target_stage = "composing"  # 回退到合成阶段
                else:
                    # 重新制作：选择回退阶段
                    target = st.selectbox("回退到哪个阶段",
                        ["重新生成配音", "重新生成数字人", "重写脚本", "换选题"],
                        key=f"target_{video['id']}")
                    instruction = st.text_area("修改原因和要求", key=f"inst2_{video['id']}")
                    stage_map = {"重新生成配音": "voice_ready", "重新生成数字人": "avatar_ready",
                                 "重写脚本": "script_ready", "换选题": "topic_selected"}
                    target_stage = stage_map[target]

                if st.form_submit_button("提交修改"):
                    submit_revision(video['id'], target_stage, instruction,
                                    dimensions if edit_mode == "minor" else [])
                    st.toast("已提交修改，Agent将重新制作")
```

#### 6.3.2 指令解析器

将自然语言修改意见解析为结构化操作，供Agent执行：

```python
# agents/revision_parser.py — 将自然语言修改意见解析为结构化操作

from services.llm import text_llm

REVISION_PARSE_PROMPT = """你是一个视频修改指令解析器。将用户的自然语言修改意见解析为结构化操作。

用户意见：{instruction}
视频信息：{video_info}

请输出JSON格式：
{{
  "actions": [
    {{
      "type": "regenerate_broll | regenerate_voice | edit_subtitle | change_music | rewrite_script",
      "target_shot": 2,  // 如果只涉及某个分镜
      "instruction": "具体的技术指令"
    }}
  ]
}}"""

async def parse_revision(instruction: str, video_info: dict) -> dict:
    result = await text_llm.chat_json([
        {"role": "system", "content": REVISION_PARSE_PROMPT.format(
            instruction=instruction, video_info=video_info
        )}
    ])
    return result
```

**修改意见映射关系：**

| 用户操作 | 回退阶段 | 影响范围 |
|----------|----------|----------|
| 轻微修改（画面/B-roll、字幕样式等） | `composing` | 仅重新合成，不重新生成素材 |
| 中度修改（配音/语气、背景音乐） | `voice_ready` / `avatar_ready` | 重新生成对应素材后重新合成 |
| 重度修改（重写脚本） | `script_ready` | 从脚本阶段重新开始全流程 |
| 换选题 | `topic_selected` | 从选题阶段重新开始 |

## 七、自动化调度

### 7.1 定时任务

```python
# scripts/daily_run.py
"""每日自动执行（通过n8n webhook触发）

n8n工作流配置：
  - Cron节点：每日08:00触发 → HTTP Request调用 /api/tasks/check_pending_scripts
  - Cron节点：每日12:00触发 → HTTP Request调用 /api/tasks/collect_data
  - Cron节点：每日18:00触发 → HTTP Request调用 /api/tasks/check_video_status
  - Cron节点：每周日20:00触发 → HTTP Request调用 /api/tasks/weekly_report

也可手动通过curl触发：
  curl -X POST http://localhost:8501/api/tasks/check_pending_scripts
"""

import requests
import os

# n8n Webhook地址（用于回调通知等）
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook")


def notify_n8n(workflow: str, payload: dict):
    """通知n8n工作流执行（用于回调触发）"""
    requests.post(f"{N8N_WEBHOOK_URL}/{workflow}", json=payload, timeout=30)
```

### 7.2 状态机

每条视频的状态流转：

```
idea → topic_selected → script_ready → storyboard_ready
    → voice_ready → avatar_ready → broll_ready
    → composing → composed → pending_review
    → approved → publishing → published
    → (或 rejected → 返回 script_ready 重新迭代)
```

数据库记录完整状态链，支持断点续作。

## 八、一键搭建步骤

### 8.1 环境准备

```bash
# 1. 安装Python 3.11+
# 2. 安装FFmpeg
sudo apt install ffmpeg
# 3. 部署n8n工作流引擎（Docker方式）
docker run -d --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=your_n8n_password \
  --restart unless-stopped \
  n8nio/n8n
# 4. 克隆项目
cd /home/liuzl/agent/YouXian-Says
# 5. 安装依赖（无需celery和redis）
pip install -r requirements.txt
# 6. 配置API Key
cp .env.example .env
# 编辑 .env 填入API Key
```

**requirements.txt 主要依赖：**

```text
# requirements.txt
fastapi
uvicorn
streamlit
pydantic-settings
openai>=1.30.0
httpx
tenacity>=8.0.0
cryptography
ffmpeg-python
playwright
sqlite-utils
python-dotenv
```

### 8.2 Phase 0 初始化

```bash
# 1. 配置方言语音（MiMo VoiceClone/TTS主线，ElevenLabs/Cartesia/OpenAI小额横评，MiniMax Speech最后兜底，均为API调用）
#    不规划本地训练模型；录音素材上传到对应官方平台或API后直接云端生成。

# 2. 配置虚拟本地人设（搭建期不强依赖HeyGen；采购后再启用API）
python scripts/create_avatar.py --mode mock

# 3. 初始化数据库
python scripts/init_db.py

# 4. 构建攸县知识库
python scripts/build_knowledge.py
```

> **启动门槛降低说明：** 主测语音方案为 MiMo VoiceClone/TTS；ElevenLabs/Cartesia/OpenAI TTS 作为小额横评；MiniMax Speech 2.8 仅作为最后兜底/基线。
> 上述方案均通过 API 直接调用，无需本地 GPU、无需声音模型训练，大幅降低 Phase 0 的启动门槛。

### 8.3 启动服务

```bash
# 启动n8n工作流引擎（如未用Docker后台运行）
# docker start n8n
# 或直接启动：
# n8n start &

# 启动Web后台（n8n通过webhook触发FastAPI接口，无需单独启动worker）
streamlit run web/app.py --server.port 8501 --server.address 127.0.0.1
```

> **n8n工作流说明：** Agent的执行通过n8n的HTTP Request节点调用FastAPI接口实现。
> daily_run.py 的定时触发由n8n的Cron节点配置，替代原有的cron/systemd timer方案。
> 无需Redis和Celery Worker进程，架构更简洁。

### 8.4 AI搭建指令

在Claude Code中执行：

```
请按照 docs/superpowers/specs/2026-05-28-youxian-tech-spec.md 的规格，
搭建攸县方言短视频制作系统。按以下顺序实施：

1. 先创建项目目录结构和配置文件
2. 实现 services/ 下的API封装（llm.py, voice.py, digital_human.py, video_gen.py, composer.py）
3. 实现 agents/ 下的三个Agent
4. 实现 web/ 下的FastAPI后端和Streamlit前端
5. 编写 scripts/ 下的安装和初始化脚本
6. 测试完整流程

每个文件实现后立即运行测试确认。
```

## 九、用户操作流程（最终版）

```
1. 打开 Web 后台 → 选题共创页
   输入："今天想聊聊攸县米粉"
   点击"发散创意" → Agent返回5个角度的选题
   选择其中2个 → 确认
        ↓ Agent自动执行 ↓
   
2. 等待通知（后台自动：脚本→分镜→配音→虚拟人设/数字人占位→图片动效/B-roll占位→合成；采购后切换到真实数字人和视频模型）
   MVP约1-2小时后，收到"视频待审核"通知；采购媒体模型后按实际渲染时间调整
        ↓
   
3. 打开审核页 → 查看分镜参考图 + 播放视频
   操作：
   - 满意 → 点击"通过"
   - 不满意 → 填写修改意见 → 点击"打回" → Agent自动迭代
        ↓
   
4. 打开发布页 → 确认发布平台和时间 → 点击"发布"
        ↓ 用户确认后分发；稳定后可切换无人值守 ↓
   
5. 数据看板自动更新，周报自动生成
```

**用户实际操作时间：MVP约40-70分钟/周；日更阶段再按实际审核量调整。**

## 十、异常处理机制

覆盖系统中8个关键异常场景，确保每个环节均有降级方案和自动恢复能力。

### 10.1 用户不提供想法（自主选题模式）

- 超过48小时未响应 -> 内容Agent基于上周数据+知识库自动生成3个选题推送
- 用户可一键确认或修改
- 选题来源优先级：上周热门话题延续 > 用户输入想法 > 知识库挖掘 > 节日/节气相关 > 方言文化传播；历史/风俗允许民间说法和爆款演绎，但需风险分级

### 10.2 选题全部否决

- Agent追问否决原因（角度不对 / 不想做这个方向 / 时间不合适）
- 基于原因自动调整策略生成第二轮不同角度选题
- 提供"快速模式"：用户直接指定支柱方向，Agent在该方向内自动出题
- 连续3轮否决后暂停，提醒用户休息后再继续

### 10.3 视频审核打回（三级回退）

| 回退级别 | 状态标记 | 回退阶段 | 影响范围 |
|----------|----------|----------|----------|
| 轻微修改 | `rejected_minor` | `composing` | 仅调整后期参数（字幕样式、B-roll位置、背景音乐等） |
| 中度修改 | `rejected_major` | `script_ready` | 重写部分段落后重新制作 |
| 重度修改 | `rejected_critical` | `topic_selected` | 更换方向，从头开始 |

**修改次数限制：** 每条视频最多2轮修改，超过则强制通过或放弃，避免无限循环。

### 10.4 HeyGen渲染失败

```python
# services/digital_human.py — HeyGen 失败降级策略

from tenacity import retry, stop_after_attempt, wait_exponential
from config.model_registry import ModelRegistry
from services.model_router import ModelRouter

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=30, max=600),  # 指数退避，最长等10分钟
)
async def create_avatar_video_with_fallback(audio_url: str, avatar_id: str) -> str:
    """生成数字人视频，失败后降级到备选方案"""
    try:
        return await create_avatar_video(audio_url, avatar_id)  # 主选：HeyGen
    except Exception as e:
        # 3次重试后降级到备选方案
        model = ModelRegistry.get_active("digital_human")
        if model.id == "heygen":
            # 自动切换到Tavus、D-ID或AKOOL
            fallback = ModelRouter().first_available(["tavus", "d_id", "akool"], "standard")
            return await _fallback_avatar_video(audio_url, avatar_id, fallback)
        raise
```

- 指数退避重试（tenacity，最多3次）
- 单条超时上限30分钟
- 3次失败后降级到备选方案（Tavus、D-ID 或 AKOOL；国内平台半自动作为人工兜底）
- 失败立即通知用户

### 10.5 配音质量不佳

- 审核页提供配音单独播放和1-5星评分
- 低于3星触发重新生成（切换参考音频或调整参数）
- 用户修改的方言表达自动记入方言优化库（`data/dialect_dict.json`）
- 重新生成时自动避开上一次使用的参考音频

### 10.6 平台发布失败

**降级链：**

```
平台官方API发布
  └─ 失败 → Playwright浏览器自动化发布
                └─ 失败 → 进入重试队列（最多3次，间隔5/15/60分钟递增）
                              └─ 3次失败 → 通知用户手动发布，提供视频下载链接
```

- Cookie过期检测：发布前校验Cookie有效性，过期时通知用户重新登录
- 重试队列持久化到数据库，服务重启不丢失

### 10.7 发布后平台审核不通过

- 48小时审核监控期，运营Agent定期检查视频状态（每4小时一次）
- 不通过时自动分析拒绝原因（标题违规 / 标签敏感 / 画面问题）
- 根据原因自动调整：
  - 标题/标签/描述问题 -> 自动修改后重新提交
  - 内容问题 -> 标记为"高风险"，反馈到选题策略，避免同类选题
- 同一视频最多重新提交2次，超过则放弃并通知用户

### 10.8 数据采集缺失

- 第三方工具（蝉妈妈等）不可用时，回退到平台自身后台数据
- 数据缺失部分在周报中标注为"估算值"
- 定义最小可用数据集：即使工具全部不可用，保留平台自有数据（播放量、点赞、评论、分享）
- 采集失败不阻塞周报生成，用已有数据 + 标注说明代替
## 十一、技术评审后的强制验收项

| 验收项 | 标准 |
|---|---|
| 未采购媒体模型也能跑通 | 未配置 `HEYGEN_API_KEY`、`RUNWAY_API_KEY` 时，仍可用 mock/local/manual 模式生成可审核成片 |
| 模型配置可视化 | 每个模型可编辑 API Base、API Key、Model Name、Channel、能力开关，并能测试连接 |
| 任务状态可恢复 | 任一视频任务都能从 `idea` 到 `published` 追踪，失败后可按阶段重试 |
| 发布前确认 | MVP默认所有发布任务进入待确认队列，不允许直接无人值守发布 |
| 方言声音授权 | 默认只有本人声音可用于生产；新增其他声音必须登记授权记录 |
| 事实风险分级 | 明确事实、民间说法、爆款演绎三类内容必须有不同风险标签 |
| 模型调用日志 | 文本、图像、语音、视频、数字人调用都必须记录模型、通道、耗时、成本、错误和质量分 |
| 数据闭环可执行 | 周报必须能回写下一周内容支柱权重和选题建议 |




