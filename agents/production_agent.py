"""Production Agent — orchestrates voice -> digital human -> B-roll -> compose -> export."""
import asyncio
import os
import json
from services.voice import generate_voice
from services.digital_human import create_digital_human
from services.video_gen import generate_broll
from services.composer import compose_video
from services.model_logger import log_model_call
from config.model_registry import ModelRegistry


class ProductionAgent:
    """制作Agent — 配音 -> 数字人 -> B-roll -> 合成 -> 多版本导出"""

    async def produce_single(self, script: dict) -> dict:
        """制作单条视频（全流程）"""
        video_id = script.get("id", script.get("video_id", "unknown"))
        job_id = "prod_" + str(video_id)

        # 1. Generate dialect voiceover
        full_text = script.get("full_dialogue") or script.get("content", "")
        voice_path = "output/voices/" + job_id + ".wav"
        voice_path = await generate_voice(full_text, voice_path, job_id=job_id)

        # 2. Generate digital human video
        dh_path = "output/videos/dh_" + job_id + ".mp4"
        dh_path = await create_digital_human(voice_path, output_path=dh_path, job_id=job_id)

        # 3. Generate B-roll clips in parallel
        shots = script.get("shots", [])
        b_roll_tasks = []
        for shot in shots:
            if shot.get("type") in ("b_roll", "broll"):
                b_roll_tasks.append(
                    generate_broll(
                        prompt=shot.get("visual_description", ""),
                        duration=shot.get("duration", 5),
                        output_path="output/videos/broll_" + job_id + "_" + str(shot.get("shot_id", 0)) + ".mp4",
                        job_id=job_id,
                    )
                )
        b_roll_paths = await asyncio.gather(*b_roll_tasks) if b_roll_tasks else []

        # 4. Compose final video (sync FFmpeg -> async via to_thread)
        b_roll_clips = [
            {
                "path": p,
                "start": shots[i].get("start_time", i * 5),
                "end": shots[i].get("start_time", i * 5) + shots[i].get("duration", 5),
            }
            for i, p in enumerate(b_roll_paths)
        ]

        subtitles = script.get("subtitles", [])
        final_path = "output/final/" + job_id + ".mp4"

        final_path = await asyncio.to_thread(
            compose_video,
            digital_human_path=dh_path,
            voice_path=voice_path,
            b_roll_clips=b_roll_clips,
            subtitles=subtitles,
            bgm_path="templates/music/bgm.mp3",
            branding_path="templates/branding/",
            output_path=final_path,
        )

        return {
            "video_path": final_path,
            "voice_path": voice_path,
            "dh_path": dh_path,
        }

    async def produce_batch(self, scripts: list[dict]) -> list[dict]:
        """批量制作视频"""
        return [await self.produce_single(s) for s in scripts]
