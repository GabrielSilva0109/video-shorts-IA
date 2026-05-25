"""
Video Engine — core processor using MoviePy + OpenCV.
Handles clip assembly, transitions and GPU detection.
"""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import List, Tuple
from loguru import logger

try:
    from moviepy.editor import (
        VideoFileClip,
        AudioFileClip,
        concatenate_videoclips,
        CompositeVideoClip,
        ColorClip,
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("MoviePy not available — using FFmpeg fallback")


def assemble_clips(
    clips: List[Path],
    audio_path: Path,
    output_path: Path,
    resolution: Tuple[int, int] = (1080, 1920),
    fps: int = 30,
) -> Path:
    """Assemble b-roll clips synced to the audio duration."""
    if not MOVIEPY_AVAILABLE:
        return _ffmpeg_assemble(clips, audio_path, output_path, resolution, fps)

    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

    audio = AudioFileClip(str(audio_path))
    total_duration = audio.duration

    if not clips:
        blank = ColorClip(size=resolution, color=(0, 0, 0), duration=total_duration)
        blank = blank.set_audio(audio)
        blank.write_videofile(str(output_path), fps=fps, logger=None)
        return output_path

    # Load + resize clips
    video_clips = []
    per_clip = total_duration / len(clips)

    for clip_path in clips:
        try:
            clip = VideoFileClip(str(clip_path)).resize(resolution)
            clip = clip.subclip(0, min(per_clip, clip.duration))
            video_clips.append(clip)
        except Exception as exc:
            logger.warning(f"Skipping clip {clip_path.name}: {exc}")

    if not video_clips:
        return _ffmpeg_assemble(clips, audio_path, output_path, resolution, fps)

    final = concatenate_videoclips(video_clips, method="compose")
    final = final.set_audio(audio)
    final.write_videofile(str(output_path), fps=fps, logger=None)

    return output_path


def apply_zoom_effect(
    clip_path: Path,
    output_path: Path,
    zoom_factor: float = 1.05,
) -> Path:
    """Apply a slow Ken Burns zoom effect."""
    if not MOVIEPY_AVAILABLE:
        return clip_path

    from moviepy.editor import VideoFileClip

    clip = VideoFileClip(str(clip_path))

    def zoom(get_frame, t):  # type: ignore[override]
        import numpy as np
        frame = get_frame(t)
        h, w = frame.shape[:2]
        factor = 1 + (zoom_factor - 1) * (t / clip.duration)
        new_w = int(w / factor)
        new_h = int(h / factor)
        x = (w - new_w) // 2
        y = (h - new_h) // 2
        cropped = frame[y : y + new_h, x : x + new_w]
        import cv2
        return cv2.resize(cropped, (w, h))

    zoomed = clip.fl(zoom)
    zoomed.write_videofile(str(output_path), logger=None)
    return output_path


def detect_gpu() -> str | None:
    """Detect available GPU encoder."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-encoders"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if "h264_nvenc" in result.stdout:
            return "nvenc"
        if "h264_videotoolbox" in result.stdout:
            return "videotoolbox"
        if "h264_vaapi" in result.stdout:
            return "vaapi"
    except Exception:
        pass
    return None


def _ffmpeg_assemble(
    clips: List[Path],
    audio_path: Path,
    output_path: Path,
    resolution: Tuple[int, int],
    fps: int,
) -> Path:
    """FFmpeg fallback for clip assembly."""
    ffmpeg = os.getenv("FFMPEG_PATH", "ffmpeg")
    w, h = resolution

    if not clips:
        subprocess.run(
            [
                ffmpeg, "-y",
                "-f", "lavfi", "-i", f"color=c=black:s={w}x{h}:r={fps}",
                "-i", str(audio_path),
                "-c:v", "libx264", "-c:a", "aac", "-shortest",
                str(output_path),
            ],
            capture_output=True,
        )
        return output_path

    concat_file = output_path.parent / "concat.txt"
    concat_file.write_text("\n".join(f"file '{p}'" for p in clips))

    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-i", str(audio_path),
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "aac", "-shortest",
            str(output_path),
        ],
        capture_output=True,
    )
    return output_path
