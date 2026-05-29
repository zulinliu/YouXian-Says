"""FFmpeg-based video composition service.

Phase 1: Full mock mode with no external API calls.
Uses subprocess.run() for complex filter_complex chains.
"""

import os
import subprocess
import tempfile
from pathlib import Path
import shutil


PROJECT_ROOT = Path(__file__).parent.parent
BRANDING_DIR = PROJECT_ROOT / "templates" / "branding"
MUSIC_DIR = PROJECT_ROOT / "templates" / "music"

DEFAULT_SUBTITLES = [
    {"start": 1.0, "end": 4.0, "text": "大家好，我系攸县人"},
    {"start": 4.5, "end": 8.0, "text": "今天我们来聊一聊攸县米粉"},
    {"start": 8.5, "end": 11.0, "text": "恰得好，耍得欢，攸县米粉最好呷"},
    {"start": 11.5, "end": 14.0, "text": "下回再来摆哈别个"},
]


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _generate_srt(subtitles: list[dict]) -> str:
    """Generate SRT subtitle file content."""
    lines = []
    for i, sub in enumerate(subtitles, 1):
        start = _seconds_to_srt_time(sub["start"])
        end = _seconds_to_srt_time(sub["end"])
        text = sub["text"]
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def _create_mock_audio(duration: float, output_path: str) -> str:
    """Generate silence audio via FFmpeg."""
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", str(duration),
        "-acodec", "pcm_s16le",
        output_path
    ], check=True, capture_output=True, text=True)
    return output_path


def _run_ffmpeg(cmd: list[str], description: str = "FFmpeg"):
    """Run FFmpeg command with error handling."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        return result
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"{description} failed: {e.stderr[:500]}")
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{description} timed out")


def compose_video(
    digital_human_path: str,
    voice_path: str,
    b_roll_clips: list[dict],
    subtitles: list[dict],
    bgm_path: str,
    branding_path: str,
    output_path: str,
    fmt: str = "9:16"
) -> str:
    """Full video composition with provided inputs."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix="youxian_compose_")
    try:
        # Generate SRT
        srt_content = _generate_srt(subtitles)
        srt_path = os.path.join(tmp_dir, "subs.srt")
        Path(srt_path).write_text(srt_content, encoding="utf-8")

        # Validate inputs exist
        for path, name in [
            (digital_human_path, "digital_human"),
            (voice_path, "voice"),
            (bgm_path, "BGM"),
            (os.path.join(branding_path, "intro.mp4"), "intro"),
            (os.path.join(branding_path, "outro.mp4"), "outro"),
            (os.path.join(branding_path, "watermark.png"), "watermark"),
        ]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"{name} not found: {path}")

        return _compose_simple(digital_human_path, voice_path, b_roll_clips,
                               subtitles, srt_path, bgm_path, branding_path,
                               output_path, tmp_dir, fmt)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _compose_simple(dh_path, voice_path, b_roll_clips, subtitles, srt_path,
                    bgm_path, branding_path, output_path, tmp_dir, fmt):
    """Simpler composition: process each layer separately, then concat."""
    total_duration = max((s["end"] for s in subtitles), default=15.0)
    total_frames = int(total_duration * 25)

    intro_path = os.path.join(branding_path, "intro.mp4")
    outro_path = os.path.join(branding_path, "outro.mp4")
    watermark_path = os.path.join(branding_path, "watermark.png")

    # Step 1: Create main content video (digital human with Ken Burns effect)
    main_raw = os.path.join(tmp_dir, "main_raw.mp4")
    _run_ffmpeg([
        "ffmpeg", "-y",
        "-loop", "1", "-i", dh_path,
        "-t", str(total_duration),
        "-vf", f"zoompan=z='min(zoom+0.0015,1.5)':d={total_frames}:s=1080x1920:fps=25",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast",
        main_raw
    ], "Create digital human base")

    # Step 2: Add subtitles
    main_subs = os.path.join(tmp_dir, "main_subs.mp4")
    srt_safe = srt_path.replace("\\", "/").replace(":", "\\:")
    try:
        _run_ffmpeg([
            "ffmpeg", "-y", "-i", main_raw,
            "-vf", f"subtitles={srt_safe}:force_style='FontName=DejaVuSans,FontSize=20,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,BorderStyle=1,Outline=2,Shadow=1'",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast",
            main_subs
        ], "Burn subtitles")
    except RuntimeError:
        # Fallback: no subtitles
        shutil.copy(main_raw, main_subs)

    # Step 3: Add watermark overlay
    main_wm = os.path.join(tmp_dir, "main_wm.mp4")
    _run_ffmpeg([
        "ffmpeg", "-y", "-i", main_subs,
        "-i", watermark_path,
        "-filter_complex", "[0:v][1:v]overlay=W-w-20:H-h-20[out]",
        "-map", "[out]", "-map", "0:a?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast",
        main_wm
    ], "Add watermark")

    # Step 4: Concat intro + main + outro
    concat_file = os.path.join(tmp_dir, "concat_list.txt")
    with open(concat_file, "w") as f:
        f.write(f"file '{intro_path}'\n")
        f.write(f"file '{main_wm}'\n")
        f.write(f"file '{outro_path}'\n")

    concat_video = os.path.join(tmp_dir, "concat_video.mp4")
    _run_ffmpeg([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        concat_video
    ], "Concat segments")

    # Step 5: Mix audio (voiceover + BGM)
    voice_audio = voice_path
    bgm_input = bgm_path
    final_audio = os.path.join(tmp_dir, "final_audio.aac")
    _run_ffmpeg([
        "ffmpeg", "-y", "-i", voice_audio,
        "-i", bgm_input,
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:weights=1 0.15[outa]",
        "-map", "[outa]", "-acodec", "aac",
        final_audio
    ], "Mix audio")

    # Step 6: Combine video + mixed audio
    _run_ffmpeg([
        "ffmpeg", "-y", "-i", concat_video,
        "-i", final_audio,
        "-c:v", "copy", "-c:a", "aac",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        output_path
    ], "Final output")

    return output_path


def compose_mock_video(
    output_path: str = None,
    duration: float = 15.0,
    voiceover_duration: float = 12.0,
    subtitle_texts: list[dict] = None,
) -> str:
    """Generate mock video using only local FFmpeg (no API calls)."""
    if output_path is None:
        output_path = str(PROJECT_ROOT / "output" / "final" / "mock_demo.mp4")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix="youxian_mock_")

    try:
        # Create mock voiceover
        voice_path = os.path.join(tmp_dir, "mock_voice.wav")
        _create_mock_audio(voiceover_duration, voice_path)

        # Use default subtitles if none provided
        subs = subtitle_texts or DEFAULT_SUBTITLES

        # Get branding assets
        branding_path = str(BRANDING_DIR)
        bgm_path = str(MUSIC_DIR / "bgm.mp3")
        dh_path = str(BRANDING_DIR / "avatar_placeholder.png")

        # Build B-roll clips from placeholder images
        broll_images = sorted(BRANDING_DIR.glob("broll_placeholder.png"))
        b_roll_clips = []
        if broll_images:
            clip_duration = 4.0
            b_roll_clips.append({
                "path": str(broll_images[0]),
                "start": 3.0,
                "end": 3.0 + clip_duration,
            })

        return compose_video(
            digital_human_path=dh_path,
            voice_path=voice_path,
            b_roll_clips=b_roll_clips,
            subtitles=subs,
            bgm_path=bgm_path,
            branding_path=branding_path,
            output_path=output_path,
            fmt="9:16"
        )

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
