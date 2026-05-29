"""Image generation service — GPT-image-2 relay mainline.

Provider priority: GPT-image-2 > Firefly/Imagen/Seedream/FLUX > MiniMax image-01 (last resort)
"""
import struct
import zlib
import logging
from pathlib import Path

from services import get_http_client
from services.model_logger import log_model_call, Timer
from config.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


def _create_minimal_png(width: int, height: int, r: int, g: int, b: int) -> bytes:
    """Create a minimal PNG file with a solid color."""
    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    # PNG signature
    sig = b"\x89PNG\r\n\x1a\n"

    # IHDR chunk
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    # IDAT chunk — uncompressed raw pixel data
    raw = b""
    for _ in range(height):
        raw += b"\x00"  # filter byte
        raw += struct.pack("BBB", r, g, b) * width
    compressed = zlib.compress(raw)

    # IEND chunk
    return sig + _chunk(b"IHDR", ihdr) + _chunk(b"IDAT", compressed) + _chunk(b"IEND", b"")


async def _mock_image(prompt: str, output_path: str, model) -> str:
    """Mock mode: generate a solid color placeholder PNG."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    # Use different colors based on prompt hash for variety
    color_hash = hash(prompt) & 0xFFFFFF
    r = (color_hash >> 16) & 0xFF
    g = (color_hash >> 8) & 0xFF
    b = color_hash & 0xFF
    png_data = _create_minimal_png(1080, 1920, r, g, b)
    with open(output_path, "wb") as f:
        f.write(png_data)
    return output_path


async def _gpt_image2(prompt: str, output_path: str, model) -> str:
    """GPT-image-2 via chat/completions endpoint (relay).

    The relay at dreamfield.top supports gpt-image-2 via chat/completions.
    Response contains markdown image reference in content field.
    """
    import base64
    import re

    client = await get_http_client()
    resp = await client.post(
        f"{model.api_base}/chat/completions",
        json={
            "model": "gpt-image-2",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 5000,
        },
        headers={"Authorization": f"Bearer {model.resolved_api_key}"},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    content = data["choices"][0]["message"]["content"]

    # Extract base64 image data from markdown image reference
    # Format: ![image_1](data:image/png;base64,...)
    match = re.search(r'data:image/[^;]+;base64,([^"\')\s]+)', content)
    if match:
        img_data = base64.b64decode(match.group(1))
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(img_data)
        return output_path

    raise ValueError("No image data found in GPT-image-2 response")


# Strategy dispatch dict — maps model.id to provider function
IMAGE_PROVIDERS = {
    "gpt_image2_relay": _gpt_image2,
    "mock": _mock_image,
}


async def generate_image(
    prompt: str, output_path: str, job_id: str = "test"
) -> str:
    """Generate image. Auto-routes to active model. Falls back to mock."""
    model = ModelRegistry.snapshot("image_gen")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if not model.resolved_api_key:
        return await _mock_image(prompt, output_path, model)

    provider_fn = IMAGE_PROVIDERS.get(model.id)
    if provider_fn is not None:
        timer = Timer()
        try:
            with timer:
                result = await provider_fn(prompt, output_path, model)
            await log_model_call(
                job_id, "image_gen", model.id, model.provider,
                channel=model.channel, latency_ms=timer.elapsed_ms, success=1,
            )
            return result
        except Exception as e:
            await log_model_call(
                job_id, "image_gen", model.id, model.provider,
                channel=model.channel, latency_ms=timer.elapsed_ms,
                success=0, error_message=str(e),
            )
            # Try fallbacks
            for fallback_id in model.fallback_ids:
                fallback_fn = IMAGE_PROVIDERS.get(fallback_id)
                if fallback_fn is None:
                    continue
                try:
                    with timer:
                        result = await fallback_fn(prompt, output_path, model)
                    await log_model_call(
                        job_id, "image_gen", fallback_id, model.provider,
                        channel=model.channel, latency_ms=timer.elapsed_ms, success=1,
                    )
                    return result
                except Exception as e:
                    logger.debug("Image fallback %s failed: %s", fallback_id, e)
                    continue
            # Ultimate fallback: mock (no exception)
            return await _mock_image(prompt, output_path, model)

    # Unregistered model ID — fallback chain
    for fallback_id in model.fallback_ids:
        fallback_fn = IMAGE_PROVIDERS.get(fallback_id)
        if fallback_fn is not None:
            try:
                return await fallback_fn(prompt, output_path, model)
            except Exception as e:
                logger.debug("Image unregistered fallback %s failed: %s", fallback_id, e)
                continue

    return await _mock_image(prompt, output_path, model)
