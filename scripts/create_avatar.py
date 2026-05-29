#!/usr/bin/env python3
"""Create virtual local persona for digital human mock mode.

Generates avatar placeholder image, persona description JSON, and
mode-selection config. Supports --mode mock|local|manual flags.
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
BRANDING_DIR = PROJECT_DIR / "templates" / "branding"

PERSONA = {
    "name": "攸攸",
    "description": "攸县本地虚拟主持人，亲切、幽默、地道",
    "personality": ["亲切", "幽默", "接地气", "知识丰富"],
    "dialect_level": "地道攸县话",
    "topics": ["美食", "风俗", "景点", "历史", "方言幽默"],
    "mode": "mock",
    "voice_authorized": False,
    "voice_owner": "",
    "authorization_note": "声音授权需要签署授权协议"
}


def create_mock_avatar():
    """Generate avatar placeholder image using FFmpeg."""
    output = BRANDING_DIR / "avatar_placeholder.png"
    os.makedirs(BRANDING_DIR, exist_ok=True)

    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=#2d2d2d:s=1080x1920:d=1",
            "-vf", "drawtext=text='数字人占位':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:fontfile=/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
            "-vframes", "1", str(output)
        ], check=True, capture_output=True, timeout=30)
        print(f"✓ Avatar placeholder image: {output}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=#2d2d2d:s=1080x1920:d=1",
            "-vframes", "1", str(output)
        ], check=True, capture_output=True, timeout=30)
        print(f"✓ Avatar placeholder (no text): {output}")


def save_persona(mode: str = "mock"):
    persona = dict(PERSONA)
    persona["mode"] = mode
    output = PROJECT_DIR / "data" / "persona.json"
    output.write_text(json.dumps(persona, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Persona saved: {output}")
    print(f"  Name: {persona['name']}")
    print(f"  Mode: {mode}")


def main():
    parser = argparse.ArgumentParser(description="创建虚拟本地人设")
    parser.add_argument("--mode", choices=["mock", "local", "manual"], default="mock",
                       help="数字人模式")
    args = parser.parse_args()

    create_mock_avatar()
    save_persona(args.mode)

    print()
    print("=== 人设创建完成 ===")
    print("当前模式:", args.mode)
    print("声音授权:", "未授权" if not PERSONA["voice_authorized"] else "已授权")


if __name__ == "__main__":
    main()
