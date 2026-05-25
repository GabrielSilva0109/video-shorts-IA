"""
AI Shorts Generator — FastAPI Application Entry Point
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes import ai, video, audio, export, templates, health
from app.utils.logging import setup_logging

setup_logging()

app = FastAPI(
    title="AI Shorts Generator API",
    description="Backend API for the AI Shorts Generator platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ─────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────
app.include_router(health.router, prefix="/api")
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(video.router, prefix="/api/video", tags=["Video"])
app.include_router(audio.router, prefix="/api/audio", tags=["Audio"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])

# ── Static exports ───────────────────────────
app.mount("/exports", StaticFiles(directory=settings.exports_dir, html=False), name="exports")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
        log_level="info",
    )
