from __future__ import annotations
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import (
    GenerationRequest,
    VideoProject,
    RenderJob,
    RenderStatus,
)
from app.models.store import store
from app.services.ai_service import AIService
from app.services.video_service import VideoService
from app.services.image_service import ImageService
from datetime import datetime

router = APIRouter()
ai_service = AIService()
video_service = VideoService()
image_service = ImageService()


# ── Projects ──────────────────────────────────
@router.get("/projects", response_model=list[VideoProject], tags=["Projects"])
async def list_projects() -> list[VideoProject]:
    return store.list_projects()


@router.get("/projects/{project_id}", response_model=VideoProject, tags=["Projects"])
async def get_project(project_id: str) -> VideoProject:
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/projects", response_model=VideoProject, tags=["Projects"])
async def create_project(
    req: GenerationRequest, background_tasks: BackgroundTasks
) -> VideoProject:
    """Create a project, generate the AI script, then kick off image generation."""
    try:
        script = await ai_service.generate_script(req.prompt, req.style, req.language)
        title = script.hook[:80] if script.hook else req.prompt[:80]
        project = VideoProject(
            title=title,
            prompt=req.prompt,
            style=req.style,
            platform=req.platform,
            script=script,
            voice_model=req.voice_model,
            subtitle_style=req.subtitle_style,
            subtitle_position=req.subtitle_position,
            background_music=req.background_music,
            effects=req.effects,
            language=req.language,
        )
        saved = store.save_project(project)

        # Generate 5 scene images in background (non-blocking)
        background_tasks.add_task(
            image_service.generate_and_save,
            project_id=saved.id,
            script=script,
            style=req.style.value,
        )

        return saved
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/projects/{project_id}", tags=["Projects"])
async def delete_project(project_id: str) -> dict:
    if not store.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": project_id}


@router.delete("/projects", tags=["Projects"])
async def delete_all_projects() -> dict:
    count = store.delete_all_projects()
    return {"deleted": count}


# ── Render ────────────────────────────────────
@router.post("/render/{project_id}", response_model=RenderJob, tags=["Render"])
async def start_render(
    project_id: str, background_tasks: BackgroundTasks
) -> RenderJob:
    project = store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = RenderJob(
        project_id=project_id,
        status=RenderStatus.queued,
        started_at=datetime.utcnow().isoformat(),
    )
    store.save_job(job)
    store.update_project(project_id, status=RenderStatus.queued, progress=0)

    background_tasks.add_task(video_service.render_project, project, job.job_id)
    return job


@router.get("/status/{job_id}", response_model=RenderJob, tags=["Render"])
async def get_render_status(job_id: str) -> RenderJob:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/render/{job_id}", tags=["Render"])
async def cancel_render(job_id: str) -> dict:
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    store.update_job(job_id, status=RenderStatus.error, error="Cancelled by user")
    return {"cancelled": job_id}
