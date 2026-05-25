"""
Audio Service — mixes background music with the narration track.
Also handles silence removal and audio normalization.
"""
from __future__ import annotations
import subprocess
import random
from pathlib import Path
from loguru import logger
from app.config import settings


class AudioService:
    MUSIC_DIR = Path("assets/music")

    def mix(
        self,
        video_path: Path,
        music_hint: str | None,
        output_dir: Path,
        music_volume: float = 0.12,
    ) -> Path:
        """Mix background music into the video at reduced volume."""
        output_path = output_dir / "with_music.mp4"
        music_path = self._resolve_music(music_hint)

        if not music_path:
            logger.info("No music found — skipping music mix")
            return video_path

        cmd = [
            settings.ffmpeg_path, "-y",
            "-i", str(video_path),
            "-stream_loop", "-1", "-i", str(music_path),
            "-filter_complex",
            f"[1:a]volume={music_volume},apad[music];"
            "[0:a][music]amix=inputs=2:duration=first:dropout_transition=3[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path),
        ]

        logger.info(f"Mixing music: {music_path.name}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"Music mix failed: {result.stderr[-300:]}")
            return video_path

        return output_path

    def _resolve_music(self, hint: str | None) -> Path | None:
        if hint and Path(hint).exists():
            return Path(hint)
        if hint and (self.MUSIC_DIR / hint).exists():
            return self.MUSIC_DIR / hint

        # Auto-select from assets/music
        if self.MUSIC_DIR.exists():
            tracks = list(self.MUSIC_DIR.glob("*.mp3")) + list(self.MUSIC_DIR.glob("*.wav"))
            if tracks:
                return random.choice(tracks)

        return None

    @staticmethod
    def normalize(audio_path: Path, output_path: Path) -> Path:
        """Loudness normalize using FFmpeg loudnorm filter."""
        cmd = [
            settings.ffmpeg_path, "-y",
            "-i", str(audio_path),
            "-af", "loudnorm=I=-14:LRA=7:TP=-2",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path

    @staticmethod
    def remove_silence(audio_path: Path, output_path: Path) -> Path:
        """Remove silent segments from audio."""
        cmd = [
            settings.ffmpeg_path, "-y",
            "-i", str(audio_path),
            "-af", "silenceremove=stop_periods=-1:stop_duration=0.3:stop_threshold=-40dB",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return output_path
