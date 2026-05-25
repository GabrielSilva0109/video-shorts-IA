from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from app.models.store import store
from app.config import settings

router = APIRouter()


@router.get("/download/{project_id}")
async def download_export(project_id: str) -> FileResponse:
    project = store.get_project(project_id)
    if not project or not project.output_path:
        raise HTTPException(status_code=404, detail="Export not found")

    path = Path(project.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(path),
        media_type="video/mp4",
        filename=f"{project.title or project_id}.mp4",
    )


@router.get("/thumbnail/{project_id}")
async def get_thumbnail(project_id: str) -> FileResponse:
    project = store.get_project(project_id)
    if not project or not project.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    path = Path(project.thumbnail_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(path=str(path), media_type="image/jpeg")
