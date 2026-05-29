"""Videos API routes with state machine enforcement."""
from fastapi import APIRouter, Depends, HTTPException
from web.auth import verify_token
from web.database import get_async_db
from web.models import VideoCreate, VideoUpdate, VideoStatusUpdate, VALID_TRANSITIONS, ModelCallLogCreate, PublishQueueCreate as PublishTaskCreate

router = APIRouter(prefix="/api/videos", tags=["videos"], dependencies=[Depends(verify_token)])


@router.get("/")
async def list_videos(db=Depends(get_async_db)):
    cursor = await db.execute("SELECT * FROM videos ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


@router.post("/")
async def create_video(video: VideoCreate, db=Depends(get_async_db)):
    cursor = await db.execute(
        "INSERT INTO videos (title, dialect_dictionary) VALUES (?, ?)",
        (video.title, video.dialect_dictionary),
    )
    await db.commit()
    return {"id": cursor.lastrowid, "title": video.title, "status": "idea"}


@router.get("/{video_id}")
async def get_video(video_id: int, db=Depends(get_async_db)):
    cursor = await db.execute("SELECT * FROM videos WHERE id=?", (video_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="视频不存在")
    return dict(row)


@router.put("/{video_id}/status")
async def update_video_status(video_id: int, update: VideoStatusUpdate, db=Depends(get_async_db)):
    """Update video status with state machine validation."""
    cursor = await db.execute("SELECT status FROM videos WHERE id=?", (video_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="视频不存在")

    current = row["status"]
    target = update.status

    if current not in VALID_TRANSITIONS:
        raise HTTPException(status_code=400, detail=f"未知的当前状态: {current}")

    if target not in VALID_TRANSITIONS.get(current, []):
        raise HTTPException(
            status_code=400,
            detail=f"不允许的状态转换: {current} → {target}. 允许的转换: {VALID_TRANSITIONS[current]}"
        )

    await db.execute(
        "UPDATE videos SET status=?, updated_at=datetime('now','localtime') WHERE id=?",
        (target, video_id),
    )
    await db.commit()
    return {"id": video_id, "status": target}


@router.post("/{video_id}/update")
async def update_video(video_id: int, update: VideoUpdate, db=Depends(get_async_db)):
    fields = []
    values = []
    if update.title:
        fields.append("title=?")
        values.append(update.title)
    if update.status:
        # State machine validation for status updates
        cursor = await db.execute("SELECT status FROM videos WHERE id=?", (video_id,))
        row = await cursor.fetchone()
        if row:
            current = row["status"]
            target = update.status
            if current in VALID_TRANSITIONS and target not in VALID_TRANSITIONS.get(current, []):
                raise HTTPException(
                    status_code=400,
                    detail=f"不允许的状态转换: {current} → {target}. 允许的转换: {VALID_TRANSITIONS[current]}"
                )
        fields.append("status=?")
        values.append(update.status)
    if update.fact_risk_level:
        fields.append("fact_risk_level=?")
        values.append(update.fact_risk_level)

    if not fields:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    fields.append("updated_at=datetime('now','localtime')")
    values.append(video_id)

    await db.execute(
        f"UPDATE videos SET {', '.join(fields)} WHERE id=?",
        values,
    )
    await db.commit()
    return {"id": video_id, "updated": update.model_dump(exclude_none=True)}


@router.post("/log-model-call")
async def log_model_call(log: ModelCallLogCreate, db=Depends(get_async_db)):
    cursor = await db.execute(
        """INSERT INTO model_call_logs (job_id, task_type, model_id, provider, channel,
           input_tokens, output_tokens, latency_ms, cost_estimate, success)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (log.job_id, log.task_type, log.model_id, log.provider, log.channel,
         log.input_tokens, log.output_tokens, log.latency_ms, log.cost_estimate, log.success),
    )
    await db.commit()
    return {"id": cursor.lastrowid}


@router.post("/publish-queue")
async def add_publish_task(task: PublishTaskCreate, db=Depends(get_async_db)):
    cursor = await db.execute(
        "INSERT INTO publish_queue (video_id, platform, scheduled_at) VALUES (?, ?, ?)",
        (task.video_id, task.platform, task.scheduled_at),
    )
    await db.commit()
    return {"id": cursor.lastrowid, **task.model_dump()}
