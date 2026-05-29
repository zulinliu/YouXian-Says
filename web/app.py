"""FastAPI backend + Streamlit frontend entrypoint.

For Streamlit UI (recommended):
  streamlit run web/streamlit_app.py --server.port 8501 --server.address 0.0.0.0

For FastAPI backend:
  uvicorn web.app:app --reload

For combined (dev only, port conflicts possible):
  streamlit run web/app.py
"""
import sys, os
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from contextlib import asynccontextmanager
from fastapi import FastAPI

# ── FastAPI Setup ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: verify database is accessible on startup."""
    try:
        import aiosqlite
        async with aiosqlite.connect("data/youxian.db") as db:
            await db.execute("SELECT 1")
        print("✓ Database accessible")
    except Exception as e:
        print(f"⚠ Database not ready: {e}. Run: python scripts/init_db.py")
    yield

app = FastAPI(title="攸县有话说 API", version="0.1.0", lifespan=lifespan)

# CORS — allow Streamlit frontend to call API
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from web.routers import auth, topics, scripts, videos
app.include_router(auth.router)
app.include_router(topics.router)
app.include_router(scripts.router)
app.include_router(videos.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ── Streamlit Entrypoint ──

def run_streamlit():
    from web.navigation import run_app
    run_app()


# When run directly with `streamlit run web/app.py`
if __name__ == "__main__":
    run_streamlit()
