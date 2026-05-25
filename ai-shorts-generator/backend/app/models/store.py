"""
Project store — persists to JSON so data survives backend reloads/restarts.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Optional, List
from app.models.schemas import VideoProject, RenderJob

_STORE_FILE = Path(__file__).parent.parent.parent / "store_data.json"


class ProjectStore:
    def __init__(self) -> None:
        self._projects: Dict[str, VideoProject] = {}
        self._jobs: Dict[str, RenderJob] = {}
        self._load()

    # ── Persistence ───────────────────────────
    def _load(self) -> None:
        if not _STORE_FILE.exists():
            return
        try:
            raw = json.loads(_STORE_FILE.read_text(encoding="utf-8"))
            self._projects = {
                k: VideoProject.model_validate(v)
                for k, v in raw.get("projects", {}).items()
            }
            self._jobs = {
                k: RenderJob.model_validate(v)
                for k, v in raw.get("jobs", {}).items()
            }
        except Exception:
            pass  # corrupt file — start fresh

    def _save(self) -> None:
        try:
            data = {
                "projects": {k: v.model_dump(mode="json") for k, v in self._projects.items()},
                "jobs": {k: v.model_dump(mode="json") for k, v in self._jobs.items()},
            }
            _STORE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    # ── Projects ──────────────────────────────
    def save_project(self, project: VideoProject) -> VideoProject:
        self._projects[project.id] = project
        self._save()
        return project

    def get_project(self, project_id: str) -> Optional[VideoProject]:
        return self._projects.get(project_id)

    def list_projects(self) -> List[VideoProject]:
        return sorted(
            self._projects.values(),
            key=lambda p: p.created_at,
            reverse=True,
        )

    def delete_project(self, project_id: str) -> bool:
        removed = self._projects.pop(project_id, None) is not None
        if removed:
            self._save()
        return removed

    def update_project(self, project_id: str, **kwargs) -> Optional[VideoProject]:
        project = self._projects.get(project_id)
        if not project:
            return None
        updated = project.model_copy(update=kwargs)
        self._projects[project_id] = updated
        self._save()
        return updated

    # ── Jobs ──────────────────────────────────
    def save_job(self, job: RenderJob) -> RenderJob:
        self._jobs[job.job_id] = job
        self._save()
        return job

    def get_job(self, job_id: str) -> Optional[RenderJob]:
        return self._jobs.get(job_id)

    def update_job(self, job_id: str, **kwargs) -> Optional[RenderJob]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        updated = job.model_copy(update=kwargs)
        self._jobs[job_id] = updated
        self._save()
        return updated

    def list_jobs(self) -> List[RenderJob]:
        return list(self._jobs.values())


# ── Singleton ─────────────────────────────────
store = ProjectStore()
