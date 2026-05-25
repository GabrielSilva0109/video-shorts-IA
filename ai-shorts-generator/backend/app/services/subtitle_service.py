"""
Subtitle Service — burns animated subtitles onto the video using FFmpeg.
Supports Hormozi bold, TikTok, clean, fire, minimal, and emoji styles.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from typing import List
from loguru import logger
from app.config import settings
from app.models.schemas import SubtitleStyle, ScriptSegment


# ── Per-style FFmpeg drawtext presets ─────────
STYLE_PRESETS: dict[str, dict] = {
    "hormozi": {
        "fontsize": 70,
        "fontcolor": "white",
        "borderw": 6,
        "bordercolor": "black",
        "bold": True,
        "box": False,
        "y_pos": "(h-text_h)/2",
    },
    "tiktok": {
        "fontsize": 60,
        "fontcolor": "white",
        "borderw": 4,
        "bordercolor": "black",
        "bold": True,
        "box": True,
        "boxcolor": "black@0.5",
        "y_pos": "h*0.75",
    },
    "clean": {
        "fontsize": 52,
        "fontcolor": "white",
        "borderw": 2,
        "bordercolor": "black@0.6",
        "bold": False,
        "box": False,
        "y_pos": "h*0.80",
    },
    "fire": {
        "fontsize": 72,
        "fontcolor": "yellow",
        "borderw": 6,
        "bordercolor": "red",
        "bold": True,
        "box": False,
        "y_pos": "(h-text_h)/2",
    },
    "minimal": {
        "fontsize": 48,
        "fontcolor": "white@0.9",
        "borderw": 1,
        "bordercolor": "black@0.3",
        "bold": False,
        "box": False,
        "y_pos": "h*0.82",
    },
    "emoji": {
        "fontsize": 62,
        "fontcolor": "white",
        "borderw": 4,
        "bordercolor": "black",
        "bold": True,
        "box": True,
        "boxcolor": "black@0.4",
        "y_pos": "(h-text_h)/2",
    },
}


class SubtitleService:
    def burn(
        self,
        video_path: Path,
        voice_path: Path,
        style: SubtitleStyle | str,
        segments: List[ScriptSegment],
        output_dir: Path,
    ) -> Path:
        style_key = style.value if hasattr(style, "value") else str(style)
        preset = STYLE_PRESETS.get(style_key, STYLE_PRESETS["hormozi"])
        output_path = output_dir / "with_subtitles.mp4"

        if not segments:
            logger.warning("No segments — skipping subtitle burn")
            return video_path

        # Build SRT file
        srt_path = output_dir / "subtitles.srt"
        self._write_srt(segments, srt_path)

        # Build FFmpeg subtitles filter
        force_style = self._build_force_style(preset)
        filter_str = (
            f"subtitles='{srt_path.as_posix()}':"
            f"force_style='{force_style}'"
        )

        cmd = [
            settings.ffmpeg_path,
            "-y",
            "-i", str(video_path),
            "-vf", filter_str,
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            str(output_path),
        ]

        logger.info(f"Burning subtitles style={style_key}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg subtitle error: {result.stderr[-500:]}")
            return video_path  # Graceful fallback

        return output_path

    @staticmethod
    def _write_srt(segments: List[ScriptSegment], path: Path) -> None:
        lines = []
        for i, seg in enumerate(segments, start=1):
            start = SubtitleService._sec_to_srt(seg.start_time)
            end = SubtitleService._sec_to_srt(seg.end_time)
            text = seg.text.upper() if True else seg.text
            lines.append(f"{i}\n{start} --> {end}\n{text}\n")
        path.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def _sec_to_srt(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    @staticmethod
    def _build_force_style(preset: dict) -> str:
        parts = [
            f"FontSize={preset['fontsize']}",
            f"PrimaryColour=&H00FFFFFF",
            f"OutlineColour=&H00000000",
            f"Outline={preset['borderw']}",
            f"Bold={1 if preset.get('bold') else 0}",
            "Alignment=2",
            "MarginV=60",
        ]
        return ",".join(parts)
