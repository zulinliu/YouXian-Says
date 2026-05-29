"""Topics API routes."""
from fastapi import APIRouter, Depends
from web.auth import verify_token
from web.database import get_async_db
from web.models import TopicCreate

router = APIRouter(prefix="/api/topics", tags=["topics"], dependencies=[Depends(verify_token)])


@router.get("/")
async def list_topics(db=Depends(get_async_db)):
    cursor = await db.execute("SELECT * FROM topics ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@router.post("/")
async def create_topic(topic: TopicCreate, db=Depends(get_async_db)):
    cursor = await db.execute(
        "INSERT INTO topics (video_id, title, pillar, source) VALUES (?, ?, ?, ?)",
        (topic.video_id, topic.title, topic.pillar, topic.source),
    )
    await db.commit()
    return {"id": cursor.lastrowid, **topic.model_dump()}
