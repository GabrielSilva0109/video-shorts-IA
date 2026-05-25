from __future__ import annotations
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── OpenAI ──────────────────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_tts_model: str = "tts-1-hd"
    openai_tts_voice: str = "alloy"
    openai_whisper_model: str = "whisper-1"

    # ── Stock video ─────────────────────────
    pexels_api_key: str = ""
    pixabay_api_key: str = ""

    # ── ElevenLabs ──────────────────────────
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # ── Backend ─────────────────────────────
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    secret_key: str = "change_me_in_production"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Queue ───────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    max_concurrent_renders: int = 2

    # ── Storage ─────────────────────────────
    exports_dir: str = "./exports"
    assets_dir: str = "./assets"
    temp_dir: str = "./tmp"

    # ── Video ───────────────────────────────
    ffmpeg_path: str = "ffmpeg"
    gpu_acceleration: bool = False
    default_fps: int = 30
    default_resolution: str = "1080x1920"

    # ── Features ────────────────────────────
    enable_batch_render: bool = True
    enable_local_ai: bool = False
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    @field_validator("openai_api_key", mode="after")
    @classmethod
    def reject_placeholder_key(cls, v: str) -> str:
        """Treat common placeholder values as unset."""
        if v in ("", "sk-...", "your_openai_key_here", "sk-your-key-here"):
            return ""
        return v

    @field_validator("exports_dir", "assets_dir", "temp_dir", mode="after")
    @classmethod
    def ensure_dir(cls, v: str) -> str:
        Path(v).mkdir(parents=True, exist_ok=True)
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def resolution_tuple(self) -> tuple[int, int]:
        w, h = self.default_resolution.split("x")
        return int(w), int(h)


settings = Settings()
