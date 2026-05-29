"""LLM unified service — auto-routes to active model from ModelRegistry."""
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
        """根据当前激活模型，返回对应的异步API client和模型名

        注意：MiMo provider 使用 api-key header 而非 Bearer token，
        所以 MiMo 模型需要特殊处理。中转站模型（zhipu_relay, openai_relay 等）
        走标准 OpenAI 兼容接口。
        """
        model = ModelRegistry.snapshot(self.function_id)
        api_key = model.resolved_api_key or os.environ.get(model.api_key_env, "")

        # 兜底：从 settings 对象直接获取（应对 streamlit 热加载场景）
        if not api_key:
            try:
                from config.settings import settings as _settings
                api_key = getattr(_settings, model.api_key_env.lower(), "")
            except Exception:
                pass

        # MiMo models use api-key header (not Bearer), handled in chat()
        if model.provider == "xiaomi":
            return None, model.model_name, model

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=model.api_base
        )
        return client, model.model_name, model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    )
    async def chat(self, messages: list, **kwargs) -> str:
        """通用聊天接口，自动路由，含重试"""
        client, model_name, model = self._get_client()

        # MiMo models use api-key header with chat/completions directly via httpx
        if model.provider == "xiaomi":
            import httpx
            async with httpx.AsyncClient(timeout=60) as hc:
                resp = await hc.post(
                    f"{model.api_base}/chat/completions",
                    json={"model": model_name, "messages": messages, **kwargs},
                    headers={"api-key": model.resolved_api_key},
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]

        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

    async def chat_json(self, messages: list, **kwargs) -> dict:
        """JSON格式输出，含容错解析"""
        content = await self.chat(
            messages,
            response_format={"type": "json_object"},
            **kwargs
        )
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"LLM 返回非法 JSON: {content[:200]}")


# 全局实例
text_llm = LLMAbstract("text_llm")
multimodal_llm = LLMAbstract("multimodal")
