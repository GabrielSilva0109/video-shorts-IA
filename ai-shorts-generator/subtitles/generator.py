"""
Subtitle generator — standalone SRT/ASS generator with word-level timing.
Uses OpenAI Whisper for forced alignment.
"""
from __future__ import annotations
from pathlib import Path
from typing import List
import json


def generate_srt(
    audio_path: Path,
    output_path: Path,
    language: str = "en",
) -> Path:
    """Generate SRT subtitles from audio using Whisper."""
    try:
        import whisper  # type: ignore[import]

        model = whisper.load_model("base")
        result = model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
        )

        lines = []
        idx = 1
        for segment in result["segments"]:
            start = _sec_to_srt(segment["start"])
            end = _sec_to_srt(segment["end"])
            text = segment["text"].strip().upper()
            lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
            idx += 1

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    except ImportError:
        raise RuntimeError("OpenAI Whisper not installed. Run: pip install openai-whisper")


def generate_word_srt(
    audio_path: Path,
    output_path: Path,
    language: str = "en",
    words_per_card: int = 3,
) -> Path:
    """Generate word-level SRT for animated subtitle cards."""
    try:
        import whisper

        model = whisper.load_model("base")
        result = model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True,
        )

        all_words: List[dict] = []
        for segment in result["segments"]:
            for word in segment.get("words", []):
                all_words.append({
                    "word": word["word"].strip().upper(),
                    "start": word["start"],
                    "end": word["end"],
                })

        # Group into cards of N words
        lines = []
        for i in range(0, len(all_words), words_per_card):
            group = all_words[i : i + words_per_card]
            if not group:
                continue
            start = _sec_to_srt(group[0]["start"])
            end = _sec_to_srt(group[-1]["end"])
            text = " ".join(w["word"] for w in group)
            lines.append(f"{i // words_per_card + 1}\n{start} --> {end}\n{text}\n")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    except ImportError:
        raise RuntimeError("OpenAI Whisper not installed")


def _sec_to_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("audio", help="Path to audio file")
    p.add_argument("--output", default="subtitles.srt")
    p.add_argument("--language", default="en")
    p.add_argument("--words", type=int, default=3, help="Words per subtitle card")
    args = p.parse_args()

    out = generate_word_srt(
        Path(args.audio),
        Path(args.output),
        args.language,
        args.words,
    )
    print(f"Subtitles → {out}")
