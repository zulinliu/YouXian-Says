"""Voice generation service — strategy dispatch via ModelRegistry.

Provider priority: MiMo VoiceClone > MiMo VoiceDesign > MiMo TTS >
ElevenLabs > Cartesia > OpenAI TTS > MiniMax Speech (last resort)
"""
import logging
import subprocess
from pathlib import Path

from services import get_http_client
from services.model_logger import log_model_call, Timer
from config.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


async def _mock_tts(text: str, output_path: str, model) -> str:
    """Mock mode: generate silence audio via FFmpeg."""
    duration = min(30, max(1, len(text) // 10))
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", str(duration),
            "-acodec", "pcm_s16le",
            output_path,
        ],
        check=True, capture_output=True,
    )
    return output_path


async def _mimo_tts(text: str, output_path: str, model) -> str:
    """MiMo TTS / VoiceClone / VoiceDesign API call.

    MiMo TTS uses chat/completions endpoint with api-key header (not Bearer).
    Response contains base64-encoded audio in message.audio.data field.
    """
    import base64
    client = await get_http_client()

    # Determine the correct model ID for the TTS model
    # Using mimo-v2.5-tts for general TTS since voiceclone requires reference audio
    tts_model = "mimo-v2.5-tts"

    resp = await client.post(
        f"{model.api_base}/chat/completions",
        json={
            "model": tts_model,
            "messages": [
                {"role": "assistant", "content": text}
            ],
        },
        headers={"api-key": model.resolved_api_key},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    # Extract base64 audio data from response
    audio_data = data["choices"][0]["message"]["audio"]["data"]
    wav_bytes = base64.b64decode(audio_data)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(wav_bytes)
    return output_path


async def _external_tts(text: str, output_path: str, model) -> str:
    """External TTS providers (ElevenLabs, Cartesia, OpenAI)."""
    client = await get_http_client()
    resp = await client.post(
        f"{model.api_base}/v1/audio/speech",
        json={"model": model.model_name, "input": text, "voice": "alloy"},
        headers={"Authorization": f"Bearer {model.resolved_api_key}"},
        timeout=60,
    )
    resp.raise_for_status()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return output_path


async def _minimax_tts(text: str, output_path: str, model) -> str:
    """MiniMax Speech 2.8 — last resort/baseline only."""
    logger.warning("MiniMax TTS invoked (last resort) for voice generation")
    client = await get_http_client()
    resp = await client.post(
        f"{model.api_base}/t2a_v2",
        json={
            "model": "Speech-2.8",
            "text": text,
            "voice_setting": {"voice_id": "yuxian_dialect_clone", "speed": 1.0},
        },
        headers={"Authorization": f"Bearer {model.resolved_api_key}"},
        timeout=60,
    )
    resp.raise_for_status()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(resp.content)
    return output_path


# Strategy dispatch dict — maps model.id to provider function
VOICE_PROVIDERS = {
    "mimo_voiceclone": _mimo_tts,
    "mimo_tts": _mimo_tts,
    "mimo_voicedesign": _mimo_tts,
    "elevenlabs_tts": _external_tts,
    "cartesia_tts": _external_tts,
    "openai_tts": _external_tts,
    "minimax_speech": _minimax_tts,
    "mock": _mock_tts,
}


async def generate_voice(
    text: str, output_path: str, job_id: str = "test"
) -> str:
    """Generate dialect voiceover. Auto-routes to active model via dispatch dict."""
    model = ModelRegistry.snapshot("voice_clone")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # If no API key, use mock mode
    if not model.resolved_api_key:
        result = await _mock_tts(text, output_path, model)
        await log_model_call(
            job_id, "voice", model.id, model.provider,
            channel=model.channel, success=1,
        )
        return result

    # Try the active provider
    provider_fn = VOICE_PROVIDERS.get(model.id)
    if provider_fn is not None:
        timer = Timer()
        try:
            with timer:
                result = await provider_fn(text, output_path, model)
            await log_model_call(
                job_id, "voice", model.id, model.provider,
                channel=model.channel, latency_ms=timer.elapsed_ms, success=1,
            )
            return result
        except Exception as e:
            await log_model_call(
                job_id, "voice", model.id, model.provider,
                channel=model.channel, latency_ms=timer.elapsed_ms,
                success=0, error_message=str(e),
            )
            # Try fallbacks before giving up
            for fallback_id in model.fallback_ids:
                fallback_fn = VOICE_PROVIDERS.get(fallback_id)
                if fallback_fn is None:
                    continue
                try:
                    with timer:
                        result = await fallback_fn(text, output_path, model)
                    await log_model_call(
                        job_id, "voice", fallback_id, model.provider,
                        channel=model.channel, latency_ms=timer.elapsed_ms, success=1,
                    )
                    return result
                except Exception as e:
                    logger.debug("Voice fallback %s failed: %s", fallback_id, e)
                    continue
            raise

    # Unregistered model: try fallbacks
    for fallback_id in model.fallback_ids:
        fallback_fn = VOICE_PROVIDERS.get(fallback_id)
        if fallback_fn is not None:
            timer = Timer()
            try:
                with timer:
                    result = await fallback_fn(text, output_path, model)
                await log_model_call(
                    job_id, "voice", fallback_id, model.provider,
                    channel=model.channel, latency_ms=timer.elapsed_ms, success=1,
                )
                return result
            except Exception as e:
                logger.debug("Voice unregistered fallback %s failed: %s", fallback_id, e)
                continue

    # Ultimate fallback: mock
    logger.warning("No registered voice provider available, falling back to mock")
    return await _mock_tts(text, output_path, model)
