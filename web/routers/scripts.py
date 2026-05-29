"""Scripts API routes."""
from fastapi import APIRouter, Depends
from web.auth import verify_token
from web.database import get_async_db
from web.models import ScriptCreate, StoryboardCreate

router = APIRouter(prefix="/api/scripts", tags=["scripts"], dependencies=[Depends(verify_token)])


@router.get("/")
async def list_scripts(db=Depends(get_async_db)):
    cursor = await db.execute("SELECT * FROM scripts ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@router.post("/")
async def create_script(script: ScriptCreate, db=Depends(get_async_db)):
    cursor = await db.execute(
        "INSERT INTO scripts (video_id, content, title, dialect_words) VALUES (?, ?, ?, ?)",
        (script.video_id, script.content, script.title, script.dialect_words),
    )
    await db.commit()
    return {"id": cursor.lastrowid, **script.model_dump()}


@router.post("/storyboards")
async def create_storyboard(sb: StoryboardCreate, db=Depends(get_async_db)):
    cursor = await db.execute(
        "INSERT INTO storyboards (video_id, shots) VALUES (?, ?)",
        (sb.video_id, sb.shots),
    )
    await db.commit()
    return {"id": cursor.lastrowid, **sb.model_dump()}
