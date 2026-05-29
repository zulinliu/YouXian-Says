"""Tests for mock pipeline verification."""
import os
import shutil
from pathlib import Path
import pytest
from services.composer import (
    compose_mock_video, compose_video,
    _generate_srt, _seconds_to_srt_time
)

pytestmark = pytest.mark.skipif(
    not shutil.which("ffprobe"),
    reason="ffprobe not available"
)


def test_generate_srt_valid_format():
    """Test that _generate_srt produces valid SRT format."""
    subtitles = [
        {"start": 1.0, "end": 4.5, "text": "大家好"},
        {"start": 5.0, "end": 10.0, "text": "今天聊米粉"},
    ]
    srt = _generate_srt(subtitles)
    assert "1" in srt[:5]
    assert "00:00:01,000 --> 00:00:04,500" in srt
    assert "00:00:05,000 --> 00:00:10,000" in srt
    assert "大家好" in srt
    assert "今天聊米粉" in srt


def test_seconds_to_srt_time():
    """Test that _seconds_to_srt_time converts correctly."""
    assert _seconds_to_srt_time(0) == "00:00:00,000"
    assert _seconds_to_srt_time(1.0) == "00:00:01,000"
    assert _seconds_to_srt_time(61.5) == "00:01:01,500"
    assert _seconds_to_srt_time(3661.0) == "01:01:01,000"


@pytest.mark.slow
def test_mock_pipeline_creates_video(tmp_path):
    """Test that compose_mock_video produces a playable MP4 file."""
    output = tmp_path / "test_mock.mp4"
    result = compose_mock_video(output_path=str(output), duration=3.0)
    assert Path(result).exists()
    assert Path(result).stat().st_size > 50_000


@pytest.mark.slow
def test_mock_pipeline_no_api_keys(tmp_path, monkeypatch):
    """Test that mock pipeline runs without any API keys configured (CHECK-01)."""
    for key in ['DEEPSEEK_API_KEY', 'MINIMAX_API_KEY', 'MIMO_API_KEY',
                'HEYGEN_API_KEY', 'RUNWAY_API_KEY', 'OPENAI_API_KEY',
                'ANTHROPIC_API_KEY', 'OPENAI_RELAY_API_KEY']:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('ADMIN_PASSWORD', 'test_pass')

    output = tmp_path / 'mock_no_keys.mp4'
    result = compose_mock_video(output_path=str(output), duration=3.0)
    assert Path(result).exists()
    assert Path(result).stat().st_size > 50_000
