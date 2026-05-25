"""
Subtitle styles — ASS style definitions for each preset.
"""
from __future__ import annotations

# ASS style header
ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""

STYLES: dict[str, str] = {
    "hormozi": (
        "Style: Default,Arial Black,80,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,"
        "1,0,0,0,100,100,0,0,1,6,0,2,10,10,80,1"
    ),
    "tiktok": (
        "Style: Default,Arial,68,&H00FFFFFF,&H000000FF,&H00000000,&H60000000,"
        "1,0,0,0,100,100,0,0,1,4,0,2,10,10,60,1"
    ),
    "clean": (
        "Style: Default,Helvetica Neue,58,&H00FFFFFF,&H000000FF,&H40000000,&H00000000,"
        "0,0,0,0,100,100,0,0,1,2,0,2,20,20,50,1"
    ),
    "fire": (
        "Style: Default,Impact,84,&H0000FFFF,&H000000FF,&H000000FF,&H80000000,"
        "1,0,0,0,100,100,0,0,1,7,0,2,10,10,80,1"
    ),
    "minimal": (
        "Style: Default,Inter,52,&H00FFFFFF,&H000000FF,&H30000000,&H00000000,"
        "0,0,0,0,100,100,0,0,1,1,0,2,30,30,50,1"
    ),
    "emoji": (
        "Style: Default,Noto Color Emoji,64,&H00FFFFFF,&H000000FF,&H00000000,&H60000000,"
        "1,0,0,0,100,100,2,0,1,4,0,2,10,10,70,1"
    ),
}


def get_ass_style(style_name: str) -> str:
    """Return full ASS style block for the given style."""
    style = STYLES.get(style_name, STYLES["hormozi"])
    return ASS_HEADER + style + "\n"
