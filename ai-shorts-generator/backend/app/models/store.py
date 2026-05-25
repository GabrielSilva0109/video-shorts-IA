"""
In-memory project store — replace with a real database (SQLite/PostgreSQL) in production.
"""
from __future__ import annotations
from typing import Dict, Optional, List
from app.models.schemas import VideoProject, RenderJob


class ProjectStore:
    def __init__(self) -> None:
        self._projects: Dict[str, VideoProject] = {}
        self._jobs: Dict[str, RenderJob] = {}

    # ── Projects ──────────────────────────────
    def save_project(self, project: VideoProject) -> VideoProject:
        self._projects[project.id] = project
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
        return self._projects.pop(project_id, None) is not None

    def update_project(self, project_id: str, **kwargs) -> Optional[VideoProject]:
        project = self._projects.get(project_id)
        if not project:
            return None
        updated = project.model_copy(update=kwargs)
        self._projects[project_id] = updated
        return updated

    # ── Jobs ──────────────────────────────────
    def save_job(self, job: RenderJob) -> RenderJob:
        self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[RenderJob]:
        return self._jobs.get(job_id)

    def update_job(self, job_id: str, **kwargs) -> Optional[RenderJob]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        updated = job.model_copy(update=kwargs)
        self._jobs[job_id] = updated
        return updated

    def list_jobs(self) -> List[RenderJob]:
        return list(self._jobs.values())


# ── Singleton ─────────────────────────────────
store = ProjectStore()
