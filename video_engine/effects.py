"""
Video Effects — punch in/out, flash, color grading, motion blur.
"""
from __future__ import annotations
import subprocess
import os
from pathlib import Path


FFMPEG = os.getenv("FFMPEG_PATH", "ffmpeg")


def punch_in_out(video_path: Path, output_path: Path) -> Path:
    """Add dramatic punch-in zoom at strategic points."""
    # Simple implementation: zoom in to 110% then back
    vf = (
        "zoompan=z='if(between(t,0,0.5),1+0.1*t/0.5,if(between(t,0.5,1.0),"
        "1.1-0.1*(t-0.5)/0.5,1))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        "d=1:s=1080x1920:fps=30"
    )
    cmd = [
        FFMPEG, "-y", "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264", "-c:a", "copy", "-preset", "fast",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        return video_path
    return output_path


def cinematic_transition(
    clip_a: Path,
    clip_b: Path,
    output_path: Path,
    transition: str = "fade",
    duration: float = 0.3,
) -> Path:
    """Apply a transition between two clips."""
    offset = 0.3
    vf = (
        f"[0:v][1:v]xfade=transition={transition}:duration={duration}"
        f":offset={offset}[v]"
    )
    cmd = [
        FFMPEG, "-y",
        "-i", str(clip_a),
        "-i", str(clip_b),
        "-filter_complex", vf,
        "-map", "[v]",
        "-c:v", "libx264",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        return clip_a
    return output_path


def color_grade(
    video_path: Path,
    output_path: Path,
    style: str = "cinematic",
) -> Path:
    """Apply a color grading look."""
    GRADES = {
        "cinematic": "curves=r='0/0 0.25/0.20 0.75/0.80 1/1':g='0/0 0.5/0.48 1/1':b='0/0 0.5/0.52 1/1'",
        "warm": "colortemperature=temperature=4500",
        "cold": "colortemperature=temperature=7000",
        "neon": "hue=s=2,curves=all='0/0 0.5/0.6 1/1'",
        "bw": "hue=s=0",
    }
    vf = GRADES.get(style, GRADES["cinematic"])
    cmd = [
        FFMPEG, "-y", "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264", "-c:a", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    return output_path if result.returncode == 0 else video_path


def add_vignette(video_path: Path, output_path: Path) -> Path:
    """Add a cinematic vignette effect."""
    cmd = [
        FFMPEG, "-y", "-i", str(video_path),
        "-vf", "vignette=PI/4",
        "-c:v", "libx264", "-c:a", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    return output_path if result.returncode == 0 else video_path
