"""Tests for multi-platform publisher service."""
import pytest

from services.publisher import (
    publish,
    PLATFORM_PROVIDERS,
    OFFICIAL_API_PLATFORMS,
    BROWSER_PLATFORMS,
)


@pytest.mark.asyncio
async def test_all_platforms_registered():
    """PLATFORM_PROVIDERS has entries for all required platforms."""
    expected = ["douyin", "kuaishou", "weixin", "xiaohongshu"]
    for platform in expected:
        assert platform in PLATFORM_PROVIDERS, f"Missing platform: {platform}"
    assert callable(PLATFORM_PROVIDERS["douyin"])


@pytest.mark.asyncio
async def test_platform_dispatch():
    """publish returns result dict for all requested platforms."""
    meta = {"title": "Test Video", "tags": ["test"], "description": "A test video"}
    result = await publish(
        "/tmp/test.mp4", meta, platforms=["douyin", "weixin"], job_id="test"
    )
    assert isinstance(result, dict)
    assert "douyin" in result
    assert "weixin" in result
    assert len(result) == 2


@pytest.mark.asyncio
async def test_official_api_simulated():
    """Douyin handler returns simulated status with pending_review."""
    meta = {"title": "Test", "tags": ["test"]}
    result = await publish(
        "/tmp/test.mp4", meta, platforms=["douyin"], job_id="test"
    )
    assert result["douyin"]["status"] == "pending_review"


@pytest.mark.asyncio
async def test_unsupported_platform():
    """Unsupported platform returns skipped status."""
    meta = {"title": "Test"}
    result = await publish(
        "/tmp/test.mp4", meta, platforms=["unknown_platform"], job_id="test"
    )
    assert result["unknown_platform"]["status"] == "skipped"
