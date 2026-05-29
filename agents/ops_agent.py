"""Ops Agent — publish, data collection, weekly report."""
import json
from datetime import datetime
from services.llm import text_llm
from services.publisher import publish
from config.prompts import get_prompt


class OpsAgent:
    """运营Agent — 发布调度 + 数据采集 + 分析报告"""

    async def publish_approved(
        self,
        video_path: str,
        platforms: list[str],
        title: str = "",
        tags: list[str] | None = None,
        description: str = "",
    ) -> dict:
        """发布已审核过的视频到指定平台"""
        return await publish(
            video_path=video_path,
            meta={"title": title, "tags": tags or [], "description": description},
            platforms=platforms,
            job_id="pub_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
        )

    async def collect_daily_data(self) -> dict:
        """模拟采集每日数据（API集成待后续）"""
        data = {"date": datetime.now().strftime("%Y-%m-%d"), "platforms": {}}
        for platform in ["douyin", "kuaishou", "weixin", "xiaohongshu"]:
            data["platforms"][platform] = {"status": "simulated"}
        return data

    async def generate_weekly_report(self, raw_data: dict | None = None) -> dict:
        """生成周度分析报告"""
        if raw_data is None:
            raw_data = await self.collect_daily_data()

        result = await text_llm.chat_json([
            {"role": "system", "content": get_prompt("weekly_report")},
            {"role": "user", "content": "本周数据：" + json.dumps(raw_data, ensure_ascii=False)}
        ])

        pillar_weights = result.get("pillar_weights", {})
        if pillar_weights:
            result["_pillar_weights_parsed"] = True
        return result
