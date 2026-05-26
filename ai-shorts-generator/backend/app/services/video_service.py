"""
Video Service — orchestrates the full render pipeline:
voice → b-roll → composite → subtitles → music → effects → export
"""
from __future__ import annotations
import asyncio
from datetime import datetime
from pathlib import Path
from loguru import logger

from app.config import settings
from app.models.schemas import VideoProject, RenderStatus
from app.models.store import store
from app.services.voice_service import VoiceService
from app.services.broll_service import BRollService
from app.services.subtitle_service import SubtitleService
from app.services.audio_service import AudioService
from app.services.export_service import ExportService


class VideoService:
    def __init__(self) -> None:
        self.voice = VoiceService()
        self.broll = BRollService()
        self.subtitles = SubtitleService()
        self.audio = AudioService()
        self.export = ExportService()

    async def render_project(self, project: VideoProject, job_id: str) -> None:
        """Full async render pipeline."""
        tmp = Path(settings.temp_dir) / project.id
        tmp.mkdir(parents=True, exist_ok=True)

        def step(status: RenderStatus, pct: int, label: str) -> None:
            store.update_project(project.id, status=status, progress=pct)
            store.update_job(job_id, status=status, progress=pct, current_step=label)
            logger.info(f"[{project.id}] {label} ({pct}%)")

        try:
            # 1. Voice narration
            step(RenderStatus.generating_voice, 10, "Generating voice narration…")
            voice_path = await self.voice.generate(
                text=project.script.full_text,  # type: ignore[union-attr]
                model=project.voice_model,
                output_dir=tmp,
                language=getattr(project, "language", "pt"),
            )

            # 2. B-roll footage
            step(RenderStatus.fetching_broll, 25, "Fetching B-roll footage…")
            broll_clips = await self.broll.fetch(
                keywords=self._extract_keywords(project.prompt, project.script),
                count=5,
                output_dir=tmp,
            )

            # 3. Composite video
            step(RenderStatus.compositing, 45, "Compositing video…")
            raw_video = await asyncio.to_thread(
                self.export.composite,
                voice_path=voice_path,
                clips=broll_clips,
                output_dir=tmp,
                project=project,
            )

            # 4. Subtitles
            step(RenderStatus.adding_subtitles, 60, "Burning subtitles…")
            with_subs = await asyncio.to_thread(
                self.subtitles.burn,
                video_path=raw_video,
                voice_path=voice_path,
                style=project.subtitle_style,
                segments=project.script.segments,  # type: ignore[union-attr]
                output_dir=tmp,
                position=getattr(project, "subtitle_position", "center"),
            )

            # 5. Background music
            step(RenderStatus.adding_music, 72, "Adding background music…")
            with_music = await asyncio.to_thread(
                self.audio.mix,
                video_path=with_subs,
                music_hint=project.background_music,
                output_dir=tmp,
            )

            # 6. Effects
            step(RenderStatus.applying_effects, 85, "Applying effects…")
            with_fx = await asyncio.to_thread(
                self.export.apply_effects,
                video_path=with_music,
                effects=project.effects,
                output_dir=tmp,
            )

            # 7. Export final
            step(RenderStatus.exporting, 93, "Exporting final video…")
            final_path, thumb_path = await asyncio.to_thread(
                self.export.finalize,
                video_path=with_fx,
                project=project,
                output_dir=Path(settings.exports_dir),
            )

            # Done
            store.update_project(
                project.id,
                status=RenderStatus.done,
                progress=100,
                output_path=str(final_path),
                thumbnail_path=str(thumb_path),
                updated_at=datetime.utcnow().isoformat(),
            )
            store.update_job(
                job_id,
                status=RenderStatus.done,
                progress=100,
                current_step="Done!",
                completed_at=datetime.utcnow().isoformat(),
            )
            logger.success(f"[{project.id}] Render complete → {final_path}")

        except Exception as exc:
            logger.exception(f"[{project.id}] Render failed: {exc}")
            store.update_project(project.id, status=RenderStatus.error, error=str(exc))
            store.update_job(
                job_id,
                status=RenderStatus.error,
                error=str(exc),
                completed_at=datetime.utcnow().isoformat(),
            )

    @staticmethod
    def _extract_keywords(prompt: str, script=None) -> list[str]:
        stop = {
            "the", "a", "an", "in", "on", "at", "of", "and", "or", "is", "are", "to", "for",
            "it", "its", "this", "that", "with", "from", "was", "has", "have", "had",
            "but", "not", "you", "your", "we", "our", "they", "their",
            # Portuguese
            "que", "em", "de", "do", "da", "no", "na", "os", "as", "um", "uma",
            "se", "por", "ao", "dos", "das", "me", "te", "lhe", "sua", "seu",
            "mais", "mas", "como", "para", "com", "ele", "ela", "isso", "ser",
        }

        def _clean(text: str) -> list[str]:
            return [
                w.strip(".,!?;:\"'()[]")
                for w in text.lower().split()
                if len(w) > 3 and w.strip(".,!?;:\"'()[]").lower() not in stop
            ]

        keywords = list(dict.fromkeys(_clean(prompt)))[:4]
        if script and getattr(script, "segments", None):
            seg_text = " ".join(s.text for s in script.segments[:10])
            extras = [w for w in _clean(seg_text) if w not in keywords]
            keywords += list(dict.fromkeys(extras))[:4]
        return keywords[:8]
