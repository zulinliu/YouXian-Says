"""Tests for digital human service."""
import pytest
from pathlib import Path

from services.digital_human import (
    create_digital_human,
    DIGITAL_HUMAN_PROVIDERS,
)


@pytest.mark.asyncio
async def test_all_modes_registered():
    """DIGITAL_HUMAN_PROVIDERS has entries for all required modes."""
    expected = ["mock", "local", "manual", "heygen", "tavus", "d_id", "akool"]
    for mode in expected:
        assert mode in DIGITAL_HUMAN_PROVIDERS, f"Missing mode: {mode}"
    assert callable(DIGITAL_HUMAN_PROVIDERS["mock"])


@pytest.mark.asyncio
async def test_manual_mode_returns_json(tmp_output_dir):
    """Manual mode writes a JSON instruction file instead of video."""
    from tests.test_services.conftest import MockModelOption
    from config import model_registry as mr

    original_snapshot = mr.ModelRegistry.snapshot

    def manual_snap(function_id):
        return MockModelOption(id="manual", provider="manual")

    mr.ModelRegistry.snapshot = manual_snap

    try:
        # Create a dummy audio file first
        audio_path = str(tmp_output_dir / "test_audio.wav")
        with open(audio_path, "wb") as f:
            f.write(b"dummy audio data")

        result = await create_digital_human(
            audio_path, output_path=str(tmp_output_dir / "dh_manual.mp4"), job_id="test"
        )
        assert result.endswith(".json"), f"Expected .json output, got: {result}"
        assert Path(result).exists(), f"JSON output file does not exist: {result}"

        import json
        with open(result, encoding="utf-8") as f:
            data = json.load(f)
        assert "audio_path" in data
        assert "message" in data
        assert "Manual upload required" in data["message"]
    finally:
        mr.ModelRegistry.snapshot = original_snapshot
