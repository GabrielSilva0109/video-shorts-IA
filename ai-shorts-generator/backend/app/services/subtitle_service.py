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
        "fontsize": 72,
        "fontcolor": "white",
        "borderw": 5,
        "bordercolor": "black",
        "bold": True,
        "box": False,
        "y_pos": "(h-text_h)/2",
    },
    "tiktok": {
        "fontsize": 62,
        "fontcolor": "white",
        "borderw": 4,
        "bordercolor": "black",
        "bold": True,
        "box": True,
        "boxcolor": "black@0.5",
        "y_pos": "h*0.75",
    },
    "clean": {
        "fontsize": 54,
        "fontcolor": "white",
        "borderw": 2,
        "bordercolor": "black@0.6",
        "bold": False,
        "box": False,
        "y_pos": "h*0.80",
    },
    "fire": {
        "fontsize": 74,
        "fontcolor": "yellow",
        "borderw": 5,
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
        "fontsize": 64,
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
        position: str = "center",
    ) -> Path:
        style_key = style.value if hasattr(style, "value") else str(style)
        preset = STYLE_PRESETS.get(style_key, STYLE_PRESETS["hormozi"])
        output_path = output_dir / "with_subtitles.mp4"

        if not segments:
            logger.warning("No segments — skipping subtitle burn")
            return video_path

        # Split long segments into punchy short lines (max 5 words)
        segments = self._split_long_segments(segments)

        # Write ASS file with correct 1080×1920 play resolution
        ass_path = output_dir / "subtitles.ass"
        self._write_ass(segments, ass_path, preset, position)

        # Also write SRT for external tools
        srt_path = output_dir / "subtitles.srt"
        self._write_srt(segments, srt_path)

        filter_str = f"ass='{ass_path.as_posix()}'"

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

    @staticmethod
    def _write_ass(segments: List[ScriptSegment], path: Path, preset: dict, position: str = "center") -> None:
        """Write an ASS file with PlayResX=1080 / PlayResY=1920 so fontsize is in real pixels."""
        play_w, play_h = 1080, 1920
        fontsize   = preset.get("fontsize", 55)
        outline_w  = preset.get("borderw", 4)
        bold       = 1 if preset.get("bold") else 0

        # Alignment and vertical margin based on position
        pos_map = {
            "top":    (8, 40),   # top-center
            "center": (5, 0),    # middle-center
            "bottom": (2, 80),   # bottom-center
        }
        alignment, margin_v = pos_map.get(position, (5, 0))

        def _c(color: str, fallback: str = "&H00FFFFFF") -> str:
            """Convert color name to ASS &HAABBGGRR."""
            table = {
                "white": "&H00FFFFFF", "white@0.9": "&H1AFFFFFF",
                "black": "&H00000000", "black@0.6": "&H99000000",
                "black@0.3": "&H4D000000",
                "yellow": "&H0000FFFF",
                "red":    "&H000000FF",
            }
            return table.get(color, fallback)

        primary    = _c(preset.get("fontcolor", "white"))
        outline_c  = _c(preset.get("bordercolor", "black"), "&H00000000")
        back_color = "&H80000000" if preset.get("box") else "&H00000000"

        header = (
            "[Script Info]\n"
            "ScriptType: v4.00+\n"
            f"PlayResX: {play_w}\n"
            f"PlayResY: {play_h}\n"
            "ScaledBorderAndShadow: yes\n"
            "\n"
            "[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
            "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
            "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
            "Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: Default,Arial,{fontsize},{primary},&H000000FF,"
            f"{outline_c},{back_color},"
            f"{bold},0,0,0,100,100,1,0,1,{outline_w},0,"
            f"{alignment},30,30,{margin_v},1\n"
            "\n"
            "[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        )
        events = []
        for seg in segments:
            start = SubtitleService._sec_to_ass(seg.start_time)
            end   = SubtitleService._sec_to_ass(seg.end_time)
            text  = seg.text.upper()
            events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

        path.write_text(header + "\n".join(events), encoding="utf-8")

    @staticmethod
    def _sec_to_ass(seconds: float) -> str:
        h  = int(seconds // 3600)
        m  = int((seconds % 3600) // 60)
        s  = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    @staticmethod
    def _split_long_segments(
        segments: List[ScriptSegment], max_words: int = 4
    ) -> List[ScriptSegment]:
        """Split segments longer than max_words into shorter, punchier subtitle lines."""
        result: List[ScriptSegment] = []
        for seg in segments:
            words = seg.text.split()
            if len(words) <= max_words:
                result.append(seg)
                continue
            chunks = [words[i : i + max_words] for i in range(0, len(words), max_words)]
            total_dur = seg.end_time - seg.start_time
            sec_per_word = total_dur / max(len(words), 1)
            t = seg.start_time
            for chunk in chunks:
                chunk_dur = len(chunk) * sec_per_word
                result.append(
                    ScriptSegment(
                        text=" ".join(chunk),
                        start_time=round(t, 3),
                        end_time=round(t + chunk_dur, 3),
                        is_bold=seg.is_bold,
                        is_hook=seg.is_hook,
                    )
                )
                t += chunk_dur
        return result
