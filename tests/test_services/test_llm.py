"""Tests for LLM service — structure, mock routing, JSON mode."""
import pytest
from services.llm import LLMAbstract, text_llm, multimodal_llm


class TestLLMStructure:
    """Test LLM service structure and imports (no API key needed)."""

    def test_llmabstract_importable(self):
        llm = LLMAbstract("text_llm")
        assert llm.function_id == "text_llm"
        assert hasattr(llm, "chat")
        assert hasattr(llm, "chat_json")

    def test_text_llm_global_instance(self):
        assert text_llm is not None
        assert text_llm.function_id == "text_llm"

    def test_multimodal_llm_global_instance(self):
        assert multimodal_llm is not None
        assert multimodal_llm.function_id == "multimodal"

    def test_chat_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(LLMAbstract.chat)

    def test_chat_json_is_async(self):
        import inspect
        assert inspect.iscoroutinefunction(LLMAbstract.chat_json)

    def test_retry_decorator_present(self):
        """Verify tenacity retry is applied to the chat method."""
        bound_chat = LLMAbstract.__dict__["chat"]
        assert hasattr(bound_chat, "retry")

    def test_get_client_structure(self, monkeypatch):
        """Test that _get_client returns expected types."""
        # ModelRegistry.snapshot needs a resolved API key to construct AsyncOpenAI
        from tests.test_services.conftest import MockModelOption
        from config import model_registry as mr

        original_snapshot = mr.ModelRegistry.snapshot

        def mock_snap(function_id):
            return MockModelOption(
                id="text_llm",
                api_base="https://api.deepseek.com",
                model_name="deepseek-chat",
                resolved_api_key="sk-test-dummy",
            )

        mr.ModelRegistry.snapshot = mock_snap
        try:
            llm = LLMAbstract("text_llm")
            client, model_name, model = llm._get_client()
            if model.provider != "xiaomi":
                from openai import AsyncOpenAI
                assert isinstance(client, AsyncOpenAI)
            assert isinstance(model_name, str)
            assert len(model_name) > 0
        finally:
            mr.ModelRegistry.snapshot = original_snapshot


@pytest.mark.api
class TestLLMWithAPI:
    """Tests that require actual API keys — skipped by default.

    Run with: python3 -m pytest -x -m api --no-header tests/
    """

    async def test_chat_returns_string(self):
        llm = LLMAbstract("text_llm")
        result = await llm.chat([
            {"role": "system", "content": "Say 'hello'"},
            {"role": "user", "content": "test"}
        ], max_tokens=50)
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_chat_json_returns_dict(self):
        llm = LLMAbstract("text_llm")
        result = await llm.chat_json([
            {"role": "system", "content": "Return {\"test\": \"value\"}"},
            {"role": "user", "content": "test"}
        ], max_tokens=100)
        assert isinstance(result, dict)
