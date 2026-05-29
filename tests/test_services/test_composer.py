"""Tests for FFmpeg composer service."""
import pytest
import os, tempfile, json
from services.composer import (
    compose_video, compose_mock_video,
    _generate_srt, _seconds_to_srt_time
)


class TestSRTGeneration:

    def test_seconds_to_srt_zero(self):
        assert _seconds_to_srt_time(0) == "00:00:00,000"

    def test_seconds_to_srt_simple(self):
        assert _seconds_to_srt_time(1.5) == "00:00:01,500"

    def test_seconds_to_srt_long(self):
        assert _seconds_to_srt_time(3661.0) == "01:01:01,000"

    def test_generate_srt_single(self):
        srt = _generate_srt([{"start": 1.0, "end": 4.5, "text": "你好"}])
        assert "00:00:01,000 --> 00:00:04,500" in srt
        assert "你好" in srt

    def test_generate_srt_multiple(self):
        subs = [
            {"start": 1.0, "end": 4.5, "text": "第一句"},
            {"start": 5.0, "end": 10.0, "text": "第二句"},
        ]
        srt = _generate_srt(subs)
        assert "1" in srt
        assert "2" in srt
        assert "第一句" in srt
        assert "第二句" in srt

    def test_generate_srt_dialect_word(self):
        """Translation field in subtitle dict is accepted but not rendered in SRT."""
        srt = _generate_srt([{"start": 1.0, "end": 3.0, "text": "好恰", "translation": "好吃"}])
        assert "好恰" in srt
        # Translation field exists in the subtitle dict but _generate_srt only uses "text"
        # This is by design — SRT displays the dialect text; translation is metadata


class TestComposerImports:

    def test_compose_video_importable(self):
        assert callable(compose_video)

    def test_compose_mock_video_importable(self):
        assert callable(compose_mock_video)


@pytest.mark.slow
class TestMockPipeline:

    def test_mock_video_creates_file(self, tmp_path):
        output = tmp_path / "test_mock.mp4"
        result = compose_mock_video(output_path=str(output), duration=3.0)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 50000

    def test_mock_video_resolution(self, tmp_path):
        import subprocess, json
        output = tmp_path / "test_res.mp4"
        compose_mock_video(output_path=str(output), duration=3.0)
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "stream=width,height", "-of", "json", str(output)],
            capture_output=True, text=True
        )
        data = json.loads(probe.stdout)
        assert data["streams"][0]["width"] == 1080
        assert data["streams"][0]["height"] == 1920

    def test_mock_video_no_api_keys(self, monkeypatch, tmp_path):
        """CHECK-01 repeated: mock pipeline needs zero API keys."""
        for key in ['DEEPSEEK_API_KEY', 'MINIMAX_API_KEY', 'MIMO_API_KEY',
                    'HEYGEN_API_KEY', 'RUNWAY_API_KEY']:
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv('ADMIN_PASSWORD', 'test_pass')

        output = tmp_path / "mock_no_keys.mp4"
        result = compose_mock_video(output_path=str(output), duration=3.0)
        assert os.path.exists(result)
        assert os.path.getsize(result) > 50000
