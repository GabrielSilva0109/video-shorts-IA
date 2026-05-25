"""
Export Service — composites b-roll clips, applies effects and exports
the final 9:16 video in H.264.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import List
from loguru import logger
from app.config import settings
from app.models.schemas import VideoProject, VideoEffects


class ExportService:
    # ── 1. Composite b-roll + voice ──────────
    def composite(
        self,
        voice_path: Path,
        clips: List[Path],
        output_dir: Path,
        project: VideoProject,
    ) -> Path:
        output_path = output_dir / "composite.mp4"
        w, h = settings.resolution_tuple  # 1080x1920

        if not clips:
            # Generate blank black video
            cmd = [
                settings.ffmpeg_path, "-y",
                "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={settings.default_fps}",
                "-i", str(voice_path),
                "-c:v", "libx264", "-c:a", "aac",
                "-shortest", str(output_path),
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path

        # Build concat input list
        concat_list = output_dir / "concat.txt"
        with concat_list.open("w") as f:
            for clip in clips:
                f.write(f"file '{clip.as_posix()}'\n")

        # Scale + pad each clip to 9:16 then concat
        scale_filter = (
            f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},setsar=1"
        )

        cmd = [
            settings.ffmpeg_path, "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-i", str(voice_path),
            "-vf", scale_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]

        logger.info("Compositing b-roll clips")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Composite error: {result.stderr[-500:]}")
            raise RuntimeError("Video composite failed")

        return output_path

    # ── 2. Apply effects ─────────────────────
    def apply_effects(
        self,
        video_path: Path,
        effects: VideoEffects,
        output_dir: Path,
    ) -> Path:
        output_path = output_dir / "with_effects.mp4"
        filters: list[str] = []

        if effects.auto_zoom:
            filters.append(
                "zoompan=z='if(lte(zoom,1.0),1.05,max(1.001,zoom-0.0015))':"
                "d=125:s=1080x1920:fps=30"
            )

        if effects.background_blur:
            filters.append(
                "[0:v]split[main][blur];"
                "[blur]scale=1080:1920,gblur=sigma=20[blurred];"
                "[blurred][main]overlay=(W-w)/2:(H-h)/2"
            )

        if not filters:
            return video_path

        vf = ",".join(f for f in filters if "[" not in f)

        cmd = [
            settings.ffmpeg_path, "-y",
            "-i", str(video_path),
            *((["-vf", vf]) if vf else []),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "copy",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"Effects error: {result.stderr[-300:]}")
            return video_path

        return output_path

    # ── 3. Final export + thumbnail ──────────
    def finalize(
        self,
        video_path: Path,
        project: VideoProject,
        output_dir: Path,
    ) -> tuple[Path, Path]:
        safe_title = "".join(
            c if c.isalnum() or c in " _-" else "_" for c in (project.title or project.id)
        )[:60]
        final_path = output_dir / f"{safe_title}.mp4"
        thumb_path = output_dir / f"{safe_title}_thumb.jpg"

        w, h = settings.resolution_tuple

        # ── Export final video ──────────────
        cmd_video = [
            settings.ffmpeg_path, "-y",
            "-i", str(video_path),
            "-c:v", "libx264",
            "-profile:v", "high",
            "-level", "4.1",
            "-pix_fmt", "yuv420p",
            "-b:v", "4M",
            "-maxrate", "6M",
            "-bufsize", "8M",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-r", str(settings.default_fps),
            "-s", f"{w}x{h}",
            str(final_path),
        ]

        if settings.gpu_acceleration:
            cmd_video = self._enable_gpu(cmd_video)

        logger.info(f"Exporting final → {final_path.name}")
        result = subprocess.run(cmd_video, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Final export failed: {result.stderr[-500:]}")

        # ── Generate thumbnail ───────────────
        cmd_thumb = [
            settings.ffmpeg_path, "-y",
            "-i", str(final_path),
            "-ss", "00:00:01",
            "-vframes", "1",
            "-q:v", "2",
            str(thumb_path),
        ]
        subprocess.run(cmd_thumb, capture_output=True)

        return final_path, thumb_path

    @staticmethod
    def _enable_gpu(cmd: list[str]) -> list[str]:
        """Try to use NVENC for GPU acceleration."""
        try:
            idx = cmd.index("libx264")
            cmd[idx] = "h264_nvenc"
            cmd += ["-gpu", "0"]
        except ValueError:
            pass
        return cmd
