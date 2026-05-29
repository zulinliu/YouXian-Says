"""YouXian Says services package — shared httpx client singleton."""
import httpx

from services.model_logger import log_model_call, Timer

__all__ = ["get_http_client", "log_model_call", "Timer"]

_shared_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared httpx client (singleton pattern)."""
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _shared_client
