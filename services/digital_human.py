"""Digital human service — mock/local/manual/heygen/tavus/d-id/akool modes."""
import json
import logging
import subprocess
from pathlib import Path

from services import get_http_client
from services.model_logger import log_model_call, Timer
from config.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


async def _mock_digital_human(
    audio_path: str, output_path: str, model, job_id: str = "test"
) -> str:
    """Mock mode: static image + audio with Ken Burns effect via FFmpeg."""
    avatar_img = Path("templates/branding/avatar_placeholder.png")
    if not avatar_img.exists():
        raise FileNotFoundError(f"Avatar placeholder not found: {avatar_img}")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(avatar_img),
            "-i", audio_path,
            "-vf", "zoompan=z='min(zoom+0.0015,1.5)':d=375:s=1080x1920:fps=25",
            "-c:v", "libx264", "-c:a", "aac", "-shortest",
            "-pix_fmt", "yuv420p", "-preset", "fast",
            output_path,
        ],
        check=True, capture_output=True, timeout=120,
    )
    return output_path


async def _manual_instructions(
    audio_path: str, output_path: str, model, job_id: str = "test"
) -> str:
    """Manual mode: write JSON instructions file instead of generating video."""
    instructions = {
        "audio_path": audio_path,
        "avatar_id": "default",
        "avatar_notes": "Use HeyGen/剪映/腾讯智影 with this audio + avatar description",
        "message": "Manual upload required: use this audio + avatar description to generate in HeyGen/剪映/腾讯智影",
        "job_id": job_id,
        "output_path": output_path,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    json_path = output_path.replace(".mp4", ".json") if output_path.endswith(".mp4") else output_path + ".json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(instructions, f, ensure_ascii=False, indent=2)
    return json_path


async def _heygen_video(
    audio_path: str, output_path: str, model, job_id: str = "test"
) -> str:
    """HeyGen video generation via API."""
    client = await get_http_client()
    resp = await client.post(
        f"{model.api_base}/v2/video/generate",
        json={
            "avatar_id": "default",
            "audio_url": audio_path,
            "dimension": {"width": 1080, "height": 1920},
            "callback_url": None,
        },
        headers={"Authorization": f"Bearer {model.resolved_api_key}"},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", {}).get("task_id", "unknown")


async def _tavus_video(
    audio_path: str, output_path: str, model, job_id: str = "test"
) -> str:
    """Tavus API — not yet integrated."""
    raise NotImplementedError(
        "tavus API not yet integrated -- configure API key in settings and implement provider handler"
    )


async def _d_id_video(
    audio_path: str, output_path: str, model, job_id: str = "test"
) -> str:
    """D-ID API — not yet integrated."""
    raise NotImplementedError(
        "d_id API not yet integrated -- configure API key in settings and implement provider handler"
    )


async def _akool_video(
    audio_path: str, output_path: str, model, job_id: str = "test"
) -> str:
    """AKOOL API — not yet integrated."""
    raise NotImplementedError(
        "akool API not yet integrated -- configure API key in settings and implement provider handler"
    )


# Strategy dispatch dict — maps model.id to provider function
DIGITAL_HUMAN_PROVIDERS = {
    "mock": _mock_digital_human,
    "local": _mock_digital_human,
    "manual": _manual_instructions,
    "heygen": _heygen_video,
    "tavus": _tavus_video,
    "d_id": _d_id_video,
    "akool": _akool_video,
}


async def create_digital_human(
    audio_path: str,
    output_path: str = None,
    job_id: str = "test",
) -> str:
    """Create digital human video. Auto-routes to active model/mode."""
    model = ModelRegistry.snapshot("digital_human")

    if output_path is None:
        output_path = f"output/videos/dh_{job_id}.mp4"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Determine mode from model.id
    mode = model.id if model.id in DIGITAL_HUMAN_PROVIDERS else "mock"

    provider_fn = DIGITAL_HUMAN_PROVIDERS[mode]

    timer = Timer()
    try:
        with timer:
            result = await provider_fn(audio_path, output_path, model, job_id=job_id)

        await log_model_call(
            job_id, "digital_human", model.id, model.provider,
            channel=model.channel, latency_ms=timer.elapsed_ms, success=1,
        )
        return result
    except NotImplementedError:
        # Try fallback
        for fallback_id in model.fallback_ids:
            fallback_fn = DIGITAL_HUMAN_PROVIDERS.get(fallback_id)
            if fallback_fn is None:
                continue
            try:
                with timer:
                    result = await fallback_fn(audio_path, output_path, model, job_id=job_id)
                await log_model_call(
                    job_id, "digital_human", fallback_id, model.provider,
                    channel=model.channel, latency_ms=timer.elapsed_ms, success=1,
                )
                return result
            except NotImplementedError:
                continue
        raise
    except Exception as e:
        await log_model_call(
            job_id, "digital_human", model.id, model.provider,
            channel=model.channel, latency_ms=timer.elapsed_ms,
            success=0, error_message=str(e),
        )
        raise
