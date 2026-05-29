"""Tests for RevisionParser."""
import pytest
from unittest.mock import patch, AsyncMock
from agents.revision_parser import parse_revision


@pytest.mark.asyncio
async def test_parse_revision_returns_dict():
    with patch("agents.revision_parser.text_llm") as mock_llm:
        mock_llm.chat_json = AsyncMock(return_value={"actions": []})
        result = await parse_revision("把第二个分镜的配音改短一点")
        assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_parse_revision_accepts_video_info():
    with patch("agents.revision_parser.text_llm") as mock_llm:
        mock_llm.chat_json = AsyncMock(return_value={"actions": []})
        result = await parse_revision("换一个背景音乐", {"title": "测试视频"})
        assert isinstance(result, dict)
