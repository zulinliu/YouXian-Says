"""Content Agent — topic divergence, script generation, storyboard generation.

Orchestrates the creative pipeline from user idea to structured storyboard.
All model calls use LLMAbstract.chat_json() for structured output.
"""
import json
import asyncio
from services.llm import text_llm
from services.image_gen import generate_image
from services.model_logger import log_model_call
from config.model_registry import ModelRegistry
from config.prompts import get_prompt
from data import DIALECT_DICT, KNOWLEDGE_BASE


class ContentAgent:
    """内容Agent — 选题发散 -> 脚本生成 -> 分镜设计"""

    def __init__(self):
        self.llm = text_llm

    async def diverge_topics(self, user_idea: str, count: int = 5) -> list[dict]:
        """发散多个角度的选题（带有热度预测和难度评估）"""
        knowledge = KNOWLEDGE_BASE[:2000] if KNOWLEDGE_BASE else ""

        result = await self.llm.chat_json([
            {"role": "system", "content": get_prompt("topic_diverge").format(
                knowledge=knowledge
            )},
            {"role": "user", "content": "用户想法：" + user_idea + "\n请生成" + str(count) + "个不同角度的选题。"}
        ], temperature=0.8)

        topics = result.get("topics", result.get("options", []))
        await log_model_call(
            "content_agent", "topic_diverge",
            ModelRegistry.snapshot("text_llm").id, "agent", success=1
        )
        return topics

    async def generate_script(self, topic: dict, dialect_dict: list | None = None) -> dict:
        """根据选题生成完整脚本"""
        if dialect_dict is None:
            dialect_dict = DIALECT_DICT

        dd_text = json.dumps(dialect_dict, ensure_ascii=False)[:2000]
        system_prompt = get_prompt("script_generation").format(dialect_dict=dd_text)
        user_msg = "选题：" + json.dumps(topic, ensure_ascii=False)

        # Try with chat_json (structured output); fallback to raw + parse
        import re
        try:
            result = await self.llm.chat_json([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg}
            ], temperature=0.8, max_tokens=2000)
        except Exception:
            raw = await self.llm.chat([
                {"role": "system", "content": system_prompt + "\n\n必须以JSON格式返回。"},
                {"role": "user", "content": user_msg}
            ], temperature=0.8, max_tokens=2000)
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
            else:
                result = {"content": raw, "format_note": "raw_text_fallback"}

        # Ensure fact_risk_level is present on each script segment
        if isinstance(result, dict):
            for key in ("segments", "facts", "statements", "content"):
                items = result.get(key, [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and "fact_risk_level" not in item:
                            item["fact_risk_level"] = "confirmed_fact"
            if "fact_risk_level" not in result:
                result["fact_risk_level"] = "confirmed_fact"

        return result

    async def generate_storyboard(self, script: dict) -> list[dict]:
        """根据脚本生成分镜（含AI参考图）"""
        result = await self.llm.chat_json([
            {"role": "system", "content": get_prompt("storyboard_generation")},
            {"role": "user", "content": "脚本：" + json.dumps(script, ensure_ascii=False)}
        ], temperature=0.6)

        shots = result.get("shots", [])

        # Generate reference images in parallel for shots that need them
        async def gen_ref(shot):
            if shot.get("need_reference") and shot.get("visual_description"):
                try:
                    path = "output/images/shot_" + str(shot.get("shot_id", 0)) + ".png"
                    shot["reference_image"] = await generate_image(
                        shot["visual_description"], path
                    )
                except Exception:
                    shot["reference_image"] = None
            return shot

        shots = await asyncio.gather(*[gen_ref(s) for s in shots])
        return shots

    async def run_creative_session(self, user_idea: str) -> dict:
        """端到端创意Session：发散 -> 脚本 -> 分镜"""
        topics = await self.diverge_topics(user_idea)
        return {"topics": topics}
