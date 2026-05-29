"""Model call logging utility — logs all model invocations to model_call_logs table."""
import time
import logging
from web.database import DB_PATH

logger = logging.getLogger(__name__)


async def log_model_call(
    job_id: str,
    task_type: str,
    model_id: str,
    provider: str,
    channel: str = "unknown",
    input_tokens: int = 0,
    output_tokens: int = 0,
    latency_ms: int = 0,
    cost_estimate: float = 0.0,
    success: int = 1,
    error_message: str | None = None,
    quality_score: float | None = None,
):
    """Log a model call to the database.

    Strips API keys from error messages before logging (T-03-01 mitigation).
    Handles database errors gracefully — logs a warning instead of raising.
    """
    import aiosqlite

    # Strip sensitive patterns from error message (T-03-01)
    safe_error = error_message
    if safe_error:
        import re
        safe_error = re.sub(
            r'(api[_-]?key|secret|token|authorization|bearer)\s*[:=]\s*\S+',
            r'\1: ***',
            safe_error,
            flags=re.IGNORECASE,
        )

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA busy_timeout=5000")
            await db.execute(
                """INSERT INTO model_call_logs
                   (job_id, task_type, model_id, provider, channel,
                    input_tokens, output_tokens, latency_ms, cost_estimate,
                    success, error_message, quality_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (job_id, task_type, model_id, provider, channel,
                 input_tokens, output_tokens, latency_ms, cost_estimate,
                 success, safe_error, quality_score),
            )
            await db.commit()
    except Exception as e:
        logger.warning("Failed to log model call: %s", e)


class Timer:
    """Simple timer context manager for measuring latency."""
    def __init__(self):
        self.start: float = 0.0
        self.elapsed_ms: int = 0

    def __enter__(self):
        self.start = time.monotonic()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = int((time.monotonic() - self.start) * 1000)
