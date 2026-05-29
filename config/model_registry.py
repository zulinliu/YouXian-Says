"""模型注册中心 — 多模型注册、切换、参数编辑与加密持久化"""

import os
import copy
import json
import base64
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from cryptography.fernet import Fernet


# ─── 数据模型 ───


@dataclass
class ModelOption:
    """单个模型选项"""
    id: str
    name: str
    provider: str
    api_base: str
    model_name: str
    api_key_env: str
    cost_per_m_tokens: float = 0
    max_context: int = 0
    channel: str = "official"
    modalities: list[str] = field(default_factory=list)
    quality_tier: str = "normal"
    cost_tier: str = "normal"
    latency_tier: str = "normal"
    data_policy: str = "standard"
    api_compatibility: str = ""
    supports_json: bool = False
    supports_tools: bool = False
    supports_image_edit: bool = False
    supports_reference_image: bool = False
    supports_9_16: bool = False
    fallback_ids: list[str] = field(default_factory=list)
    notes: str = ""
    resolved_api_key: str = ""


@dataclass
class FunctionSlot:
    """一个功能维度的所有可选模型"""
    function_id: str
    function_name: str
    options: list[ModelOption] = field(default_factory=list)
    active_id: str = ""


# ─── API Key 加密/解密/脱敏 工具函数 ───


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


# ─── 全局模型注册表 ───

REGISTRY: dict[str, FunctionSlot] = {

    "text_llm": FunctionSlot(
        function_id="text_llm",
        function_name="文本LLM（选题/脚本/分镜/分析）",
        active_id="deepseek_v4_flash",
        options=[
            ModelOption(
                id="deepseek_v4_flash", name="DeepSeek V4 Flash",
                provider="deepseek", api_base="${DEEPSEEK_BASE_URL}",
                model_name="DeepSeek-V4-Flash", api_key_env="DEEPSEEK_API_KEY",
                cost_per_m_tokens=0, max_context=1_000_000,
                channel="official", modalities=["text", "tool"],
                quality_tier="draft", cost_tier="low", latency_tier="fast",
                api_compatibility="openai_chat", supports_json=True, supports_tools=True,
                notes="批量低成本任务：选题池、标题、标签、日报"
            ),
            ModelOption(
                id="deepseek_v4pro", name="DeepSeek V4 Pro",
                provider="deepseek", api_base="${DEEPSEEK_BASE_URL}",
                model_name="deepseek-v4-pro", api_key_env="DEEPSEEK_API_KEY",
                cost_per_m_tokens=6, max_context=1_000_000,
                channel="official", modalities=["text", "tool"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="openai_chat", supports_json=True, supports_tools=True,
                notes="深度推理第三顺位；稳定中文定稿、脚本、分镜、周报"
            ),
            ModelOption(
                id="mimo_v2_5", name="MiMo V2.5",
                provider="xiaomi", api_base="${MIMO_BASE_URL}",
                model_name="mimo-v2.5", api_key_env="MIMO_API_KEY",
                cost_per_m_tokens=0, max_context=1_000_000,
                channel="official", modalities=["text", "tool"],
                quality_tier="draft", cost_tier="low",
                notes="批量低成本中文草稿和二路备选"
            ),
            ModelOption(
                id="mimo_v2_5_pro", name="MiMo V2.5 Pro",
                provider="xiaomi", api_base="${MIMO_BASE_URL}",
                model_name="mimo-v2.5-pro", api_key_env="MIMO_API_KEY",
                cost_per_m_tokens=0, max_context=1_000_000,
                channel="official", modalities=["text", "tool"],
                quality_tier="high", cost_tier="normal",
                notes="长上下文整理、脚本二审、中文质量校验"
            ),
            ModelOption(
                id="glm_5_1_relay", name="GLM-5.1 Relay",
                provider="zhipu_relay", api_base="${GLM_RELAY_BASE_URL}",
                model_name="GLM-5.1", api_key_env="GLM_RELAY_API_KEY",
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
                provider="xiaomi", api_base="${MIMO_BASE_URL}",
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
                api_compatibility="openai_chat",
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
                notes="后续备选���暂不购买"
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
                provider="xiaomi", api_base="${MIMO_BASE_URL}",
                model_name="mimo-v2.5-tts-voiceclone", api_key_env="MIMO_API_KEY",
                channel="official", modalities=["audio"],
                quality_tier="high", cost_tier="normal",
                api_compatibility="native",
                fallback_ids=["mimo_voicedesign", "mimo_tts", "elevenlabs_tts", "cartesia_tts", "openai_tts", "minimax_speech"],
                notes="语音主线，优先评估攸县方言咬字、音色相似度和情绪稳定性"
            ),
            ModelOption(
                id="mimo_tts", name="MiMo V2.5 TTS",
                provider="xiaomi", api_base="${MIMO_BASE_URL}",
                model_name="mimo-v2.5-tts", api_key_env="MIMO_API_KEY",
                channel="official", modalities=["audio"],
                quality_tier="normal", cost_tier="low",
                api_compatibility="native",
                fallback_ids=["openai_tts", "elevenlabs_tts", "minimax_speech"],
                notes="草稿配音、普通旁白和低成本版本"
            ),
            ModelOption(
                id="mimo_voicedesign", name="MiMo V2.5 TTS VoiceDesign",
                provider="xiaomi", api_base="${MIMO_BASE_URL}",
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


# ─── 模型注册中心类 ───


class ModelRegistry:
    """模型注册中心 — 读取/切换/编辑参数/持久化

    持久化文件 data/model_state.json 结构：
    {
      "text_llm": {
        "active_id": "deepseek_v4pro",
        "overrides": {
          "deepseek_v4pro": {
            "api_base": "https://api.deepseek.com",
            "api_key": "encrypted_sk-xxx...",
            "model_name": "deepseek-v4-pro"
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

        # 解析 ${VAR} 环境变量引用
        import re
        def _resolve_env(value: str) -> str:
            return re.sub(r'\$\{(\w+)\}', lambda m: os.environ.get(m.group(1), m.group(0)), value)
        base.api_base = _resolve_env(base.api_base)
        base.model_name = _resolve_env(base.model_name)

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
                            api_base: str | None = None, api_key: str | None = None,
                            model_name: str | None = None):
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
            text = path.read_text().strip()
            if text:
                return json.loads(text)
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
