"""
Voice Service — generates narration audio using OpenAI TTS, ElevenLabs,
or a local Coqui TTS model.
"""
from __future__ import annotations
from pathlib import Path
import aiofiles
from loguru import logger
from openai import AsyncOpenAI
from app.config import settings
from app.models.schemas import VoiceModel


class VoiceService:
    def __init__(self) -> None:
        self._openai: AsyncOpenAI | None = None
        if settings.openai_api_key:
            self._openai = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate(
        self,
        text: str,
        model: VoiceModel | str,
        output_dir: Path,
    ) -> Path:
        model_key = model.value if hasattr(model, "value") else str(model)
        output_path = output_dir / "narration.mp3"

        logger.info(f"Generating voice with {model_key}")

        if model_key == "openai":
            await self._openai_tts(text, output_path)
        elif model_key == "elevenlabs":
            await self._elevenlabs_tts(text, output_path)
        else:
            await self._local_tts(text, output_path)

        return output_path

    async def _openai_tts(self, text: str, output_path: Path) -> None:
        if not self._openai:
            raise RuntimeError("OpenAI client not configured")
        response = await self._openai.audio.speech.create(
            model=settings.openai_tts_model,
            voice=settings.openai_tts_voice,  # type: ignore[arg-type]
            input=text,
            response_format="mp3",
        )
        async with aiofiles.open(output_path, "wb") as f:
            await f.write(response.content)

    async def _elevenlabs_tts(self, text: str, output_path: Path) -> None:
        if not settings.elevenlabs_api_key:
            raise RuntimeError("ElevenLabs API key not configured")
        import httpx

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{settings.elevenlabs_voice_id}"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                headers={
                    "xi-api-key": settings.elevenlabs_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "text": text,
                    "model_id": "eleven_turbo_v2",
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
                },
            )
            resp.raise_for_status()
            async with aiofiles.open(output_path, "wb") as f:
                await f.write(resp.content)

    async def _local_tts(self, text: str, output_path: Path) -> None:
        """Use Coqui TTS for local generation (must be installed separately)."""
        import asyncio
        import subprocess

        cmd = [
            "tts",
            "--text", text,
            "--out_path", str(output_path),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Local TTS failed: {stderr.decode()}")
