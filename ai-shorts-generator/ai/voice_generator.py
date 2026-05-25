"""
Voice generator — standalone TTS script.
"""
from __future__ import annotations
import asyncio
import os
from pathlib import Path
from openai import AsyncOpenAI


VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


async def generate_voice(
    text: str,
    output_path: str | Path = "output.mp3",
    voice: str = "alloy",
    model: str = "tts-1-hd",
    api_key: str | None = None,
) -> Path:
    key = api_key or os.getenv("OPENAI_API_KEY", "")
    client = AsyncOpenAI(api_key=key)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    response = await client.audio.speech.create(
        model=model,
        voice=voice,  # type: ignore[arg-type]
        input=text,
        response_format="mp3",
    )

    output_path.write_bytes(response.content)
    print(f"Voice saved → {output_path}")
    return output_path


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("text")
    p.add_argument("--output", default="output.mp3")
    p.add_argument("--voice", default="alloy", choices=VOICES)
    args = p.parse_args()

    asyncio.run(generate_voice(args.text, args.output, args.voice))
