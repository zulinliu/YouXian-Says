"""Multi-platform publisher — Douyin/Kuaishou API + WeChat/Xiaohongshu Playwright.

T-03-02: MVP requires human confirmation gate (pending_review -> approved);
no unattended publish by default.
"""
import logging

from services.model_logger import log_model_call, Timer

logger = logging.getLogger(__name__)

OFFICIAL_API_PLATFORMS = ["douyin", "kuaishou"]
BROWSER_PLATFORMS = ["weixin", "xiaohongshu"]


async def _douyin_api(video_path: str, meta: dict, model=None) -> dict:
    """Publish to Douyin via open API (simulated)."""
    return {
        "status": "simulated",
        "platform": "douyin",
        "message": "Douyin API call simulated -- configure API credentials for production",
    }


async def _kuaishou_api(video_path: str, meta: dict, model=None) -> dict:
    """Publish to Kuaishou via open API (simulated)."""
    return {
        "status": "simulated",
        "platform": "kuaishou",
        "message": "Kuaishou API call simulated -- configure API credentials for production",
    }


async def _weixin_playwright(video_path: str, meta: dict, model=None) -> dict:
    """Publish to WeChat Channels via Playwright automation (simulated).

    Note: Requires saved cookies with valid session.
    """
    return {
        "status": "simulated",
        "platform": "weixin",
        "note": "Playwright flow requires cookie setup and manual first-time auth",
    }


async def _xiaohongshu_playwright(video_path: str, meta: dict, model=None) -> dict:
    """Publish to Xiaohongshu via Playwright automation (simulated)."""
    return {
        "status": "simulated",
        "platform": "xiaohongshu",
        "note": "Playwright flow requires cookie setup and manual first-time auth",
    }


# Strategy dispatch dict — maps platform name to handler function
PLATFORM_PROVIDERS = {
    "douyin": _douyin_api,
    "kuaishou": _kuaishou_api,
    "weixin": _weixin_playwright,
    "xiaohongshu": _xiaohongshu_playwright,
}


async def publish(
    video_path: str,
    meta: dict,
    platforms: list[str],
    job_id: str = "test",
) -> dict:
    """Publish video to specified platforms.

    Returns {platform: result_dict} for all platforms.

    T-03-02: All publishes return "pending_review" status by default —
    actual publishing requires explicit human approval.
    """
    results = {}

    for platform in platforms:
        handler = PLATFORM_PROVIDERS.get(platform)
        if handler is None:
            results[platform] = {
                "status": "skipped",
                "reason": f"Unsupported platform: {platform}",
            }
            continue

        timer = Timer()
        try:
            with timer:
                result = await handler(video_path, meta)
            # T-03-02: Default to pending_review for unattended safety
            result["status"] = "pending_review"
            results[platform] = result

            await log_model_call(
                job_id, "publish", f"publisher_{platform}", "local",
                channel="local_tool", latency_ms=timer.elapsed_ms, success=1,
            )
        except Exception as e:
            results[platform] = {"status": "failed", "error": str(e)}
            await log_model_call(
                job_id, "publish", f"publisher_{platform}", "local",
                channel="local_tool", latency_ms=timer.elapsed_ms,
                success=0, error_message=str(e),
            )

    return results
