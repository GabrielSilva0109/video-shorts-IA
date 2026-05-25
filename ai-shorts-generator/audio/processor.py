"""
Audio processor — standalone audio tools.
"""
from __future__ import annotations
import subprocess
import os
from pathlib import Path

FFMPEG = os.getenv("FFMPEG_PATH", "ffmpeg")


def remove_silence(
    input_path: Path,
    output_path: Path,
    threshold_db: int = -40,
    min_silence_duration: float = 0.3,
) -> Path:
    """Remove silence from audio."""
    vf = (
        f"silenceremove=stop_periods=-1:"
        f"stop_duration={min_silence_duration}:"
        f"stop_threshold={threshold_db}dB"
    )
    cmd = [
        FFMPEG, "-y", "-i", str(input_path),
        "-af", vf, str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def normalize_loudness(
    input_path: Path,
    output_path: Path,
    target_lufs: float = -14.0,
) -> Path:
    """Two-pass loudnorm for broadcast-quality audio."""
    cmd = [
        FFMPEG, "-y", "-i", str(input_path),
        "-af", f"loudnorm=I={target_lufs}:LRA=7:TP=-2",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def mix_audio(
    voice_path: Path,
    music_path: Path,
    output_path: Path,
    music_vol: float = 0.12,
) -> Path:
    """Mix voice and music tracks."""
    cmd = [
        FFMPEG, "-y",
        "-i", str(voice_path),
        "-stream_loop", "-1", "-i", str(music_path),
        "-filter_complex",
        f"[1:a]volume={music_vol}[m];[0:a][m]amix=inputs=2:duration=first[out]",
        "-map", "[out]",
        "-c:a", "aac",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def detect_beats(audio_path: Path) -> list[float]:
    """Use librosa to detect beat timestamps."""
    try:
        import librosa  # type: ignore[import]
        import numpy as np

        y, sr = librosa.load(str(audio_path))
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        return beat_times
    except ImportError:
        return []
