"""Tests for ContentAgent."""
import pytest
from agents.content_agent import ContentAgent


@pytest.mark.asyncio
async def test_content_agent_initialization():
    agent = ContentAgent()
    assert agent.llm is not None
    assert hasattr(agent, "diverge_topics")
    assert hasattr(agent, "generate_script")
    assert hasattr(agent, "generate_storyboard")


@pytest.mark.asyncio
async def test_content_agent_has_run_creative_session():
    agent = ContentAgent()
    assert hasattr(agent, "run_creative_session")
    assert callable(agent.run_creative_session)


def test_content_agent_accepts_dialect_dict(mock_dialect_dict):
    agent = ContentAgent()
    assert hasattr(agent, "generate_script")
