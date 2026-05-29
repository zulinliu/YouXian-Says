"""B-roll video generation — mock/local/runway/veo/kling/luma/pika/hailuo."""
import logging
import subprocess
from pathlib import Path

from services import get_http_client
from services.model_logger import log_model_call, Timer
from config.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


async def _mock_broll(
    prompt: str, output_path: str, duration: float, model, job_id: str = "test"
) -> str:
    """Mock mode: static image with Ken Burns zoom effect via FFmpeg."""
    broll_img = Path("templates/branding/broll_placeholder.png")
    if not broll_img.exists():
        raise FileNotFoundError(f"B-roll placeholder not found: {broll_img}")

    frames = int(duration * 25)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(broll_img),
            "-t", str(duration),
            "-vf",
            f"zoompan=z='min(zoom+0.003,1.5)':d={frames}:s=1080x1920:fps=25,"
            f"fade=t=in:st=0:d=0.5,fade=t=out:st={duration - 0.5}:d=0.5",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast", output_path,
        ],
        check=True, capture_output=True, timeout=60,
    )
    return output_path


# Placeholder providers for paid API modes
async def _runway_video(
    prompt: str, output_path: str, duration: float, model, job_id: str = "test"
) -> str:
    raise NotImplementedError(
        "runway API not yet integrated -- configure API key in settings and implement provider handler"
    )


async def _veo_video(
    prompt: str, output_path: str, duration: float, model, job_id: str = "test"
) -> str:
    raise NotImplementedError(
        "veo API not yet integrated -- configure API key in settings and implement provider handler"
    )


async def _kling_video(
    prompt: str, output_path: str, duration: float, model, job_id: str = "test"
) -> str:
    raise NotImplementedError(
        "kling API not yet integrated -- configure API key in settings and implement provider handler"
    )


async def _luma_video(
    prompt: str, output_path: str, duration: float, model, job_id: str = "test"
) -> str:
    raise NotImplementedError(
        "luma API not yet integrated -- configure API key in settings and implement provider handler"
    )


async def _pika_video(
    prompt: str, output_path: str, duration: float, model, job_id: str = "test"
) -> str:
    raise NotImplementedError(
        "pika API not yet integrated -- configure API key in settings and implement provider handler"
    )


async def _hailuo_video(
    prompt: str, output_path: str, duration: float, model, job_id: str = "test"
) -> str:
    raise NotImplementedError(
        "hailuo API not yet integrated -- configure API key in settings and implement provider handler"
    )


# Strategy dispatch dict — maps model.id to provider function
VIDEO_PROVIDERS = {
    "mock": _mock_broll,
    "local": _mock_broll,
    "runway": _runway_video,
    "veo": _veo_video,
    "kling": _kling_video,
    "luma": _luma_video,
    "pika": _pika_video,
    "hailuo": _hailuo_video,
}


async def generate_broll(
    prompt: str,
    output_path: str = None,
    target_duration: float = 5.0,
    job_id: str = "test",
) -> str:
    """Generate B-roll video clip. Auto-routes to active model."""
    model = ModelRegistry.snapshot("video_gen")

    if output_path is None:
        output_path = f"output/videos/broll_{job_id}.mp4"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # For long durations (>6s), generate multiple clips and concatenate
    if target_duration > 6.0:
        logger.info("Long B-roll duration (%.1fs), splitting into clips", target_duration)
        # For mock mode, just generate a single longer clip
        pass

    provider_fn = VIDEO_PROVIDERS.get(model.id) or VIDEO_PROVIDERS.get("mock")
    if provider_fn is None:
        provider_fn = _mock_broll

    timer = Timer()
    try:
        with timer:
            result = await provider_fn(prompt, output_path, target_duration, model, job_id=job_id)

        await log_model_call(
            job_id, "video_gen", model.id, model.provider,
            channel=model.channel, latency_ms=timer.elapsed_ms, success=1,
        )
        return result
    except NotImplementedError:
        # Try fallbacks
        for fallback_id in model.fallback_ids:
            fallback_fn = VIDEO_PROVIDERS.get(fallback_id)
            if fallback_fn is None:
                continue
            try:
                with timer:
                    result = await fallback_fn(prompt, output_path, target_duration, model, job_id=job_id)
                await log_model_call(
                    job_id, "video_gen", fallback_id, model.provider,
                    channel=model.channel, latency_ms=timer.elapsed_ms, success=1,
                )
                return result
            except NotImplementedError:
                continue
        # Ultimate fallback: mock
        logger.warning("No registered video provider available, falling back to mock")
        return await _mock_broll(prompt, output_path, target_duration, model, job_id=job_id)
    except Exception as e:
        await log_model_call(
            job_id, "video_gen", model.id, model.provider,
            channel=model.channel, latency_ms=timer.elapsed_ms,
            success=0, error_message=str(e),
        )
        raise
