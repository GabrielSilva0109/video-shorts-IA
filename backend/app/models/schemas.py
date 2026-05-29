from __future__ import annotations
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


# ── Enums ─────────────────────────────────────
class VideoStyle(str, Enum):
    hormozi = "hormozi"
    tiktok_story = "tiktok_story"
    finance = "finance"
    motivation = "motivation"
    gaming = "gaming"
    luxury = "luxury"
    documentary = "documentary"


class ExportPlatform(str, Enum):
    tiktok = "tiktok"
    youtube_shorts = "youtube_shorts"
    instagram_reels = "instagram_reels"


class RenderStatus(str, Enum):
    idle = "idle"
    queued = "queued"
    generating_script = "generating_script"
    generating_voice = "generating_voice"
    fetching_broll = "fetching_broll"
    compositing = "compositing"
    adding_subtitles = "adding_subtitles"
    adding_music = "adding_music"
    applying_effects = "applying_effects"
    exporting = "exporting"
    generating_images = "generating_images"
    done = "done"
    error = "error"


class SubtitleStyle(str, Enum):
    hormozi = "hormozi"
    tiktok = "tiktok"
    clean = "clean"
    fire = "fire"
    minimal = "minimal"
    emoji = "emoji"


class SubtitlePosition(str, Enum):
    top = "top"
    center = "center"
    bottom = "bottom"


class VoiceModel(str, Enum):
    openai = "openai"
    elevenlabs = "elevenlabs"
    edge_tts = "edge_tts"
    local = "local"


# ── Domain models ─────────────────────────────
class VideoEffects(BaseModel):
    auto_zoom: bool = True
    punch_in_out: bool = True
    cinematic_transitions: bool = True
    sound_effects: bool = True
    background_blur: bool = False
    beat_sync: bool = True
    motion_graphics: bool = False


class ScriptSegment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    start_time: float
    end_time: float
    is_bold: bool = False
    is_hook: bool = False
    emoji: Optional[str] = None


class GeneratedScript(BaseModel):
    hook: str
    body: str
    cta: str
    full_text: str
    segments: List[ScriptSegment] = []
    estimated_duration: float
    word_count: int


class VideoProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    prompt: str
    style: VideoStyle
    platform: ExportPlatform
    script: Optional[GeneratedScript] = None
    voice_model: VoiceModel = VoiceModel.openai
    subtitle_style: SubtitleStyle = SubtitleStyle.hormozi
    subtitle_position: SubtitlePosition = SubtitlePosition.center
    background_music: Optional[str] = None
    effects: VideoEffects = Field(default_factory=VideoEffects)
    language: str = "pt"
    status: RenderStatus = RenderStatus.idle
    progress: int = 0
    error: Optional[str] = None
    output_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    generated_images: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RenderJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    status: RenderStatus = RenderStatus.queued
    progress: int = 0
    current_step: str = "Queued"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


# ── Request / Response schemas ─────────────────
class GenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000)
    style: VideoStyle = VideoStyle.hormozi
    platform: ExportPlatform = ExportPlatform.tiktok
    voice_model: VoiceModel = VoiceModel.openai
    subtitle_style: SubtitleStyle = SubtitleStyle.hormozi
    subtitle_position: SubtitlePosition = SubtitlePosition.center
    background_music: Optional[str] = None
    language: str = "pt"
    effects: VideoEffects = Field(default_factory=VideoEffects)
    custom_script: Optional[str] = None


class ScriptRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000)
    style: VideoStyle = VideoStyle.hormozi
    language: str = "pt"


class TitleRequest(BaseModel):
    script: str


class DescriptionRequest(BaseModel):
    script: str
    platform: str = "tiktok"


class AITitleSuggestions(BaseModel):
    titles: List[str]
    hooks: List[str]


class AIDescriptionResult(BaseModel):
    description: str
    hashtags: List[str]
    keywords: List[str]


class ImagerModel(str, Enum):
    flux_schnell = "flux_schnell"
    flux_dev = "flux_dev"


class ImagerGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=2000)
    model: ImagerModel = ImagerModel.flux_schnell
    width: int = Field(1024, ge=256, le=2048)
    height: int = Field(1024, ge=256, le=2048)
    seed: Optional[int] = Field(default=None, ge=0)


class ImagerGenerateResponse(BaseModel):
    image_url: str
    image_path: str
    model: ImagerModel
    width: int
    height: int
    seed: Optional[int] = None
