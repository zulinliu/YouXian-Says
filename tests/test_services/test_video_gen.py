"""Tests for B-roll video generation service."""
import pytest
from pathlib import Path

from services.video_gen import generate_broll, VIDEO_PROVIDERS


@pytest.mark.asyncio
async def test_provider_registry():
    """VIDEO_PROVIDERS has entries for all required providers."""
    expected = ["mock", "local", "runway", "veo", "kling", "luma", "pika", "hailuo"]
    for provider_id in expected:
        assert provider_id in VIDEO_PROVIDERS, f"Missing provider: {provider_id}"
    assert callable(VIDEO_PROVIDERS["mock"])


@pytest.mark.asyncio
async def test_fallback_to_mock(tmp_output_dir):
    """With no API key, generate_broll falls back to mock mode."""
    from tests.test_services.conftest import MockModelOption
    from config import model_registry as mr

    original_snapshot = mr.ModelRegistry.snapshot

    def mock_snap(function_id):
        return MockModelOption(id="mock")

    mr.ModelRegistry.snapshot = mock_snap

    try:
        output_path = str(tmp_output_dir / "test_broll.mp4")
        result = await generate_broll(
            "攸县街景", output_path=output_path, target_duration=3.0, job_id="test"
        )
        assert Path(result).exists(), f"Output file does not exist: {result}"
        assert result == output_path
    finally:
        mr.ModelRegistry.snapshot = original_snapshot


@pytest.mark.asyncio
async def test_long_duration(tmp_output_dir):
    """Long duration (>6s) still produces output via mock."""
    from tests.test_services.conftest import MockModelOption
    from config import model_registry as mr

    original_snapshot = mr.ModelRegistry.snapshot

    def mock_snap(function_id):
        return MockModelOption(id="mock")

    mr.ModelRegistry.snapshot = mock_snap

    try:
        output_path = str(tmp_output_dir / "test_long_broll.mp4")
        result = await generate_broll(
            "测试长视频", output_path=output_path, target_duration=10.0, job_id="test"
        )
        assert Path(result).exists()
    finally:
        mr.ModelRegistry.snapshot = original_snapshot
