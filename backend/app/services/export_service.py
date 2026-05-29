"""
Export Service — composites b-roll clips, applies effects and exports
the final 9:16 video in H.264.
"""
from __future__ import annotations
import re
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
            cmd = [
                settings.ffmpeg_path, "-y",
                "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={settings.default_fps}",
                "-i", str(voice_path),
                "-c:v", "libx264", "-c:a", "aac",
                "-shortest", str(output_path),
            ]
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path

        # Calculate per-clip duration from voice audio
        total_duration = self._get_duration(voice_path)
        per_clip = max(2.0, total_duration / len(clips))

        # Pre-process each clip: scale to 9:16 + Ken Burns pan + fade in/out
        processed: list[Path] = []
        for i, clip in enumerate(clips):
            out = output_dir / f"clip_kb_{i}.mp4"
            ok = self._preprocess_clip(
                clip_path=clip,
                output_path=out,
                index=i,
                duration=per_clip,
                apply_zoom=project.effects.auto_zoom,
            )
            processed.append(out if ok else clip)

        # Concat pre-processed clips and mix voice
        concat_list = output_dir / "concat.txt"
        with concat_list.open("w") as f:
            for clip in processed:
                f.write(f"file '{clip.resolve().as_posix()}'\n")

        cmd = [
            settings.ffmpeg_path, "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_list),
            "-i", str(voice_path),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_path),
        ]

        logger.info("Compositing pre-processed clips")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Fallback: re-encode to resolve timestamp/codec mismatches
            cmd_reenc = [
                settings.ffmpeg_path, "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_list),
                "-i", str(voice_path),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(output_path),
            ]
            result = subprocess.run(cmd_reenc, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Composite error: {result.stderr[-500:]}")
                raise RuntimeError("Video composite failed")

        return output_path

    def _preprocess_clip(
        self,
        clip_path: Path,
        output_path: Path,
        index: int,
        duration: float,
        apply_zoom: bool = True,
    ) -> bool:
        """Scale clip to 9:16, apply a subtle horizontal pan (Ken Burns) and fade in/out."""
        w, h = settings.resolution_tuple
        fps = settings.default_fps
        fade_d = min(0.30, duration * 0.08)
        fade_out_start = max(0.0, duration - fade_d)

        if apply_zoom:
            # Scale 10% larger than target to create horizontal panning room
            sw, sh = int(w * 1.10), int(h * 1.10)   # 1188 × 2112
            margin_w = sw - w                          # 108 px
            y_center = (sh - h) // 2                  # 96 px
            dur_s = f"{duration:.3f}"
            if index % 2 == 0:
                x_expr = f"'{margin_w}*t/{dur_s}'"        # pan left → right
            else:
                x_expr = f"'{margin_w}*(1-t/{dur_s})'"    # pan right → left
            scale_crop = (
                f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
                f"crop={w}:{h}:x={x_expr}:y='{y_center}',setsar=1,fps={fps}"
            )
        else:
            scale_crop = (
                f"scale={w}:{h}:force_original_aspect_ratio=increase,"
                f"crop={w}:{h},setsar=1,fps={fps}"
            )

        vf = (
            f"{scale_crop}"
            f",fade=t=in:st=0:d={fade_d:.3f}"
            f",fade=t=out:st={fade_out_start:.3f}:d={fade_d:.3f}"
        )

        cmd = [
            settings.ffmpeg_path, "-y",
            "-i", str(clip_path),
            "-t", f"{duration:.3f}",
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",
            str(output_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            if result.returncode != 0:
                logger.warning(f"Preprocess clip {index} failed: {result.stderr[-200:]}")
                return False
            return True
        except subprocess.TimeoutExpired:
            logger.warning(f"Preprocess clip {index} timed out — using original")
            return False

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
            # Subtle static zoom-in: scale 5% larger then crop back
            filters.append("scale=1134:2016,crop=1080:1920:27:48")

        # Always apply cinematic color grade
        filters.append("eq=saturation=1.35:contrast=1.08:brightness=0.03")
        # Subtle sharpen
        filters.append("unsharp=5:5:0.5:3:3:0.2")
        # Fade in from black (first 0.5 s)
        filters.append("fade=t=in:st=0:d=0.5")
        # Fade out to black (last 0.7 s)
        duration = self._get_duration(video_path)
        if duration > 1.5:
            fade_start = max(0.0, duration - 0.8)
            filters.append(f"fade=t=out:st={fade_start:.2f}:d=0.7")

        if effects.background_blur:
            # Dark-edge vignette
            filters.append("vignette=angle=PI/5:mode=backward")

        vf = ",".join(filters)

        cmd = [
            settings.ffmpeg_path, "-y",
            "-i", str(video_path),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "copy",
            str(output_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.warning(f"Effects error: {result.stderr[-300:]}")
                return video_path
            return output_path
        except subprocess.TimeoutExpired:
            logger.warning("Effects step timed out — skipping effects")
            return video_path

    def _get_duration(self, path: Path) -> float:
        """Return video duration in seconds using ffmpeg -i."""
        result = subprocess.run(
            [settings.ffmpeg_path, "-i", str(path)],
            capture_output=True, text=True,
        )
        m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", result.stderr)
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        return 0.0

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
