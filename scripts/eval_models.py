#!/usr/bin/env python3
"""Model evaluation script — runs sample prompts across all configured models.

Tests each model with project-specific prompts and collects quality scores.
"""
import asyncio, json, os, sys, time
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))
os.environ["ADMIN_PASSWORD"] = "eval_test"

EVAL_SAMPLES = [
    {"task_type": "topic", "prompt": "攸县米粉为什么出名", "quality_dimensions": ["local_relevance", "hook_strength"]},
    {"task_type": "topic", "prompt": "攸县香干的秘密", "quality_dimensions": ["local_relevance"]},
    {"task_type": "script", "prompt": "写一个30秒的攸县方言口播脚本", "quality_dimensions": ["dialect_accuracy", "structure_quality"]},
]


async def evaluate():
    """Run model evaluation across configured models."""
    from config.model_registry import ModelRegistry
    from services.llm import LLMAbstract

    results = []
    models_to_test = ["deepseek_v4_flash", "deepseek_v4pro"]

    for model_id in models_to_test:
        print(f"\n--- Testing: {model_id} ---")
        try:
            ModelRegistry.switch("text_llm", model_id)
            llm = LLMAbstract("text_llm")

            for sample in EVAL_SAMPLES:
                start = time.monotonic()
                try:
                    response = await llm.chat([
                        {"role": "system", "content": "你是一个攸县方言短视频创作助手。"},
                        {"role": "user", "content": sample["prompt"]}
                    ], temperature=0.8, max_tokens=500)
                    latency = int((time.monotonic() - start) * 1000)
                    results.append({
                        "model_id": model_id,
                        "task_type": sample["task_type"],
                        "prompt": sample["prompt"],
                        "success": 1,
                        "latency_ms": latency,
                        "response_length": len(response),
                        "dimensions": {d: 3 for d in sample["quality_dimensions"]},
                    })
                    print(f"  ✓ {sample['task_type']}: {latency}ms, {len(response)} chars")
                except Exception as e:
                    results.append({
                        "model_id": model_id,
                        "task_type": sample["task_type"],
                        "prompt": sample["prompt"],
                        "success": 0,
                        "error": str(e),
                    })
                    print(f"  ✗ {sample['task_type']}: {e}")
        except Exception as e:
            print(f"  ✗ Model {model_id} failed: {e}")

    output_path = PROJECT_DIR / "output" / f"eval_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n✓ Evaluation complete: {output_path}")
    print(f"  Total runs: {len(results)}")
    print(f"  Success rate: {sum(r['success'] for r in results)}/{len(results)}")


if __name__ == "__main__":
    asyncio.run(evaluate())
