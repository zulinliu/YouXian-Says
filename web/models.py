"""Pydantic models for API request/response validation."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Video State Machine ──

class VideoStatus(str, Enum):
    idea = "idea"
    topic_selected = "topic_selected"
    script_ready = "script_ready"
    storyboard_ready = "storyboard_ready"
    voice_ready = "voice_ready"
    avatar_ready = "avatar_ready"
    broll_ready = "broll_ready"
    composing = "composing"
    composed = "composed"
    pending_review = "pending_review"
    approved = "approved"
    publishing = "publishing"
    published = "published"
    rejected = "rejected"


VIDEO_STATUS_FLOW = [
    "idea", "topic_selected", "script_ready", "storyboard_ready",
    "voice_ready", "avatar_ready", "broll_ready",
    "composing", "composed", "pending_review",
    "approved", "publishing", "published", "rejected",
]

VALID_TRANSITIONS = {
    "idea": ["topic_selected"],
    "topic_selected": ["script_ready", "idea"],
    "script_ready": ["storyboard_ready", "topic_selected"],
    "storyboard_ready": ["voice_ready", "script_ready"],
    "voice_ready": ["avatar_ready", "script_ready"],
    "avatar_ready": ["broll_ready", "script_ready"],
    "broll_ready": ["composing", "script_ready"],
    "composing": ["composed"],
    "composed": ["pending_review"],
    "pending_review": ["approved", "rejected"],
    "approved": ["publishing"],
    "publishing": ["published"],
    "published": [],
    "rejected": ["script_ready", "topic_selected"],
}


# ── Videos ──

class VideoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    topic_id: Optional[int] = None
    script_id: Optional[int] = None
    storyboard_id: Optional[int] = None
    dialect_dictionary: Optional[str] = None
    fact_risk_level: str = "confirmed_fact"


class VideoUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    fact_risk_level: Optional[str] = None


class VideoStatusUpdate(BaseModel):
    status: str = Field(..., description="目标状态")
    note: Optional[str] = None


class VideoResponse(BaseModel):
    id: int
    title: str
    status: str
    topic_id: Optional[int] = None
    script_id: Optional[int] = None
    storyboard_id: Optional[int] = None
    dialect_dictionary: Optional[str] = None
    fact_risk_level: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ── Topics ──

class TopicCreate(BaseModel):
    video_id: int
    title: str = Field(..., min_length=1)
    pillar: Optional[str] = None
    source: str = "user"


class TopicResponse(BaseModel):
    id: int
    video_id: int
    title: str
    pillar: Optional[str] = None
    source: str
    status: str
    created_at: str

    model_config = {"from_attributes": True}


# ── Scripts ──

class ScriptCreate(BaseModel):
    video_id: int
    content: str = Field(..., min_length=1)
    title: Optional[str] = None
    dialect_words: Optional[str] = None


class ScriptResponse(BaseModel):
    id: int
    video_id: int
    content: str
    title: Optional[str] = None
    dialect_words: Optional[str] = None
    status: str
    fact_check_notes: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}


# ── Storyboards ──

class StoryboardCreate(BaseModel):
    video_id: int
    shots: str = Field(..., description="JSON string of shot list")


class StoryboardResponse(BaseModel):
    id: int
    video_id: int
    shots: str
    status: str
    created_at: str

    model_config = {"from_attributes": True}


# ── Auth ──

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Model Call Logs ──

class ModelCallLogCreate(BaseModel):
    job_id: str
    task_type: str
    model_id: str
    provider: str
    channel: str = "unknown"
    prompt_version: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cost_estimate: float = 0.0
    success: int = 0
    error_message: Optional[str] = None
    quality_score: Optional[float] = None


# ── Publish Queue ──

class PublishQueueCreate(BaseModel):
    video_id: int
    platform: str = Field(..., pattern="^(douyin|kuaishou|weixin|xiaohongshu)$")
    scheduled_at: Optional[str] = None


# ── Analytics ──

class AnalyticsDataCreate(BaseModel):
    video_id: int
    platform: str
    date: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    followers: int = 0


# ── Lifecycle & Review Models ──

class VideoLifecycleResponse(BaseModel):
    """Full lifecycle info for a video task."""
    id: int
    title: str
    status: str
    created_at: str
    updated_at: str
    allowed_transitions: list[str]

class ReviewAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    dimensions: list[str] = Field(default_factory=list)
    comment: str = ""

class ReviewResponse(BaseModel):
    id: int
    status: str
    review_actions: list[dict]

class PublishTaskStatus(BaseModel):
    id: int
    video_id: int
    platform: str
    status: str
    scheduled_at: str | None = None
    published_at: str | None = None
    retry_count: int = 0

class WeeklyReportResponse(BaseModel):
    summary: str
    top_videos: list[dict] = []
    suggestions: list[str] = []
    pillar_weights: dict = {}
