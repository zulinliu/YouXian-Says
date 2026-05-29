"""Revision Parser — converts natural language feedback to structured operations."""
from services.llm import text_llm
from config.prompts import get_prompt


async def parse_revision(instruction: str, video_info: dict = None) -> dict:
    """Parse natural language revision into structured actions.

    Returns:
        dict with "actions" list: [{type, target_shot, instruction}, ...]
    """
    context = ""
    if video_info:
        context = "\n视频信息：" + str(video_info)

    result = await text_llm.chat_json([
        {"role": "system", "content": get_prompt("revision_parse")},
        {"role": "user", "content": "用户意见：" + instruction + context}
    ])
    return result
