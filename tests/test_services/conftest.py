"""Shared fixtures for service tests."""
import pytest
import gc


class MockModelOption:
    """Minimal mock for ModelOption used in tests."""
    def __init__(
        self,
        id: str = "mock",
        name: str = "Mock Model",
        provider: str = "mock_provider",
        api_base: str = "https://mock.api",
        model_name: str = "mock-model",
        api_key_env: str = "MOCK_API_KEY",
        channel: str = "test",
        resolved_api_key: str = "",
        fallback_ids: list[str] = None,
    ):
        self.id = id
        self.name = name
        self.provider = provider
        self.api_base = api_base
        self.model_name = model_name
        self.api_key_env = api_key_env
        self.channel = channel
        self.resolved_api_key = resolved_api_key
        self.fallback_ids = fallback_ids or []


@pytest.fixture
def mock_model_option():
    """Returns a MockModelOption with no API key (triggers mock mode)."""
    return MockModelOption()


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Returns a temporary directory for generated files."""
    return tmp_path


@pytest.fixture(autouse=True)
def cleanup_fixtures():
    """Clean up after each test."""
    yield
    gc.collect()
