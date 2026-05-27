"""
Image Service — generates 5 scene images via Pollinations.ai (primary, free),
DALL-E 3, Pexels static images, or FFmpeg gradient placeholders as fallbacks.
"""
from __future__ import annotations
import asyncio
import os
import subprocess
from pathlib import Path
from typing import List, TYPE_CHECKING

import httpx
from loguru import logger

from app.config import settings
from app.models.store import store

if TYPE_CHECKING:
    from app.models.schemas import GeneratedScript


STYLE_SUFFIX: dict[str, str] = {
    "hormozi": "bold motivational quote poster, high contrast, dramatic lighting, cinematic",
    "tiktok_story": "vibrant social media scene, colorful, trending aesthetic, dynamic",
    "finance": "professional financial scene, modern office, clean minimal, charts, success",
    "motivation": "epic cinematic landscape, sunrise, powerful atmosphere, inspiring",
    "gaming": "neon gaming setup, dramatic colors, high energy, futuristic",
    "luxury": "luxury lifestyle photography, gold, elegant, aspirational, premium",
    "documentary": "documentary photography, natural light, authentic, raw, real",
}

# Pexels search terms per style for fallback
STYLE_PEXELS_QUERY: dict[str, str] = {
    "hormozi": "success motivation business",
    "tiktok_story": "lifestyle social media trendy",
    "finance": "money finance investment",
    "motivation": "inspiration sunrise nature",
    "gaming": "gaming technology neon",
    "luxury": "luxury lifestyle elegant",
    "documentary": "documentary portrait authentic",
}

# Gradient colors for FFmpeg final fallback
_GRADIENT_COLORS = [
    ("4B006E", "9B00CE"),
    ("001a4d", "0055CC"),
    ("0d2600", "1a6600"),
    ("4d0000", "CC0000"),
    ("1a1400", "554400"),
]


class ImageService:
    async def generate_and_save(
        self,
        project_id: str,
        script: "GeneratedScript",
        style: str,
    ) -> None:
        """Generate images from script and persist paths to the project store."""
        from app.models.schemas import RenderStatus
        output_dir = Path(settings.exports_dir) / project_id / "images"
        try:
            paths = await self.generate_from_script(script, style, output_dir)
            store.update_project(project_id, generated_images=paths)
            logger.success(f"[{project_id}] {len(paths)} scene images saved")
        except Exception as exc:
            logger.error(f"[{project_id}] Image generation failed: {exc}")

    async def generate_from_script(
        self,
        script: "GeneratedScript",
        style: str,
        output_dir: Path,
        count: int = 5,
    ) -> List[str]:
        """Generate images using the script structure (hook / body / cta)."""
        output_dir.mkdir(parents=True, exist_ok=True)
        prompts = self._prompts_from_script(script, style, count)
        return await self._run_pipeline(prompts, output_dir, count)

    async def generate(
        self,
        script: str,
        style: str,
        output_dir: Path,
        count: int = 5,
    ) -> List[str]:
        """Generate images from raw script text (used as legacy fallback)."""
        output_dir.mkdir(parents=True, exist_ok=True)
        prompts = self._build_prompts(script, style, count)
        return await self._run_pipeline(prompts, output_dir, count)

    async def _run_pipeline(
        self, prompts: List[str], output_dir: Path, count: int
    ) -> List[str]:
        """Try each provider and merge results — FFmpeg fills only the gaps."""
        # indexed dict so we can track which slots are filled
        results: dict[int, str] = {}

        # 1. Pollinations.ai — sequential to respect rate limits
        for i, prompt in enumerate(prompts[:count]):
            try:
                p = await self._pollinations_one(prompt, output_dir / f"img_{i}.jpg", i)
                results[i] = str(p)
                await asyncio.sleep(0.5)   # avoid 429 / rate-limit
            except Exception as exc:
                logger.warning(f"Pollinations image {i} failed: {exc}")

        logger.info(f"Pollinations: {len(results)}/{count} images generated")

        # 2. DALL-E 3 for slots still missing
        if settings.openai_api_key and len(results) < count:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            for i in [j for j in range(count) if j not in results]:
                try:
                    p = await self._dalle_one(client, prompts[i], output_dir / f"img_{i}.png", i)
                    results[i] = str(p)
                except Exception as exc:
                    logger.warning(f"DALL-E image {i} failed: {exc}")

        # 3. FFmpeg only for remaining gaps
        if len(results) < count:
            placeholder_dir = output_dir
            ffmpeg_all = self._ffmpeg_placeholders(placeholder_dir, count)
            for i, fp in enumerate(ffmpeg_all):
                if i not in results:
                    results[i] = fp
                    logger.info(f"Gap {i} filled with FFmpeg placeholder")

        return [results[i] for i in range(count) if i in results]

    # ── Pollinations.ai ───────────────────────
    async def _pollinations_one(self, prompt: str, output_path: Path, index: int) -> Path:
        from urllib.parse import quote

        encoded = quote(prompt)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=1080&height=1920&seed={index * 42}&model=flux"
        )
        async with httpx.AsyncClient(timeout=60) as http:
            resp = await http.get(url, follow_redirects=True)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)
        logger.info(f"[Pollinations {index}] saved → {output_path.name}")
        return output_path

    # ── DALL-E 3 ──────────────────────────────
    async def _dalle_one(self, client, prompt: str, output_path: Path, index: int) -> Path:
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792",
            quality="standard",
            n=1,
        )
        url = response.data[0].url  # type: ignore[index]
        async with httpx.AsyncClient(timeout=60) as http:
            resp = await http.get(url)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)
        logger.info(f"[Image {index}] saved → {output_path.name}")
        return output_path

    # ── Pexels fallback ───────────────────────
    async def _try_pexels(self, style: str, output_dir: Path, count: int) -> List[str]:
        query = STYLE_PEXELS_QUERY.get(style, "cinematic scene")
        logger.info(f"Fetching Pexels images: query='{query}'")

        try:
            async with httpx.AsyncClient(timeout=30) as http:
                resp = await http.get(
                    "https://api.pexels.com/v1/search",
                    params={"query": query, "per_page": count, "orientation": "portrait"},
                    headers={"Authorization": settings.pexels_api_key},
                )
                resp.raise_for_status()
                photos = resp.json().get("photos", [])
        except Exception as exc:
            logger.warning(f"Pexels image search failed: {exc}")
            return []

        download_tasks = [
            self._download_image(
                photo["src"]["large"],
                output_dir / f"img_{i}.jpg",
                i,
            )
            for i, photo in enumerate(photos[:count])
        ]
        results = await asyncio.gather(*download_tasks, return_exceptions=True)
        paths = [str(r) for r in results if not isinstance(r, Exception)]
        logger.info(f"Pexels: {len(paths)}/{count} images downloaded")
        return paths

    async def _download_image(self, url: str, output_path: Path, index: int) -> Path:
        async with httpx.AsyncClient(timeout=30) as http:
            resp = await http.get(url)
            resp.raise_for_status()
            output_path.write_bytes(resp.content)
        logger.info(f"[Pexels image {index}] saved → {output_path.name}")
        return output_path

    # ── FFmpeg final fallback ─────────────────
    def _ffmpeg_placeholders(self, output_dir: Path, count: int) -> List[str]:
        ffmpeg = os.getenv("FFMPEG_PATH", settings.ffmpeg_path)
        paths: List[str] = []

        for i in range(count):
            c1, c2 = _GRADIENT_COLORS[i % len(_GRADIENT_COLORS)]
            out = output_dir / f"img_{i}.png"
            cmd = [
                ffmpeg, "-y",
                "-f", "lavfi",
                "-i", (
                    f"color=c=0x{c1}:s=1080x1920:r=1,"
                    f"geq=r='lerp(16,lerp(0x{c1[:2]},0x{c2[:2]},Y/H),X/W)':"
                    f"g='lerp(16,lerp(0x{c1[2:4]},0x{c2[2:4]},Y/H),X/W)':"
                    f"b='lerp(16,lerp(0x{c1[4:]},0x{c2[4:]},Y/H),X/W)'"
                ),
                "-frames:v", "1",
                str(out),
            ]
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=15)
                if result.returncode == 0:
                    paths.append(str(out))
                else:
                    # Ultra-simple fallback: solid color PNG
                    simple_cmd = [
                        ffmpeg, "-y",
                        "-f", "lavfi", "-i", f"color=c=0x{c1}:s=1080x1920:r=1",
                        "-frames:v", "1", str(out),
                    ]
                    r2 = subprocess.run(simple_cmd, capture_output=True, timeout=10)
                    if r2.returncode == 0:
                        paths.append(str(out))
            except Exception as exc:
                logger.warning(f"FFmpeg placeholder {i} failed: {exc}")

        logger.info(f"FFmpeg placeholders: {len(paths)}/{count} created")
        return paths

    # ── Prompt builders ───────────────────────
    def _prompts_from_script(
        self, script: "GeneratedScript", style: str, count: int = 5
    ) -> List[str]:
        """Build visual prompts using the script structure: hook / body points / cta."""
        suffix = STYLE_SUFFIX.get(style, "cinematic, high quality")

        # Collect sections: hook → body segments → cta
        sections: List[str] = []

        # 1. Hook — opening visual
        if script.hook:
            sections.append(script.hook.strip())

        # 2. Body — extract key sentences (split on ". " or use segments)
        body_text = script.body or script.full_text
        if script.segments and len(script.segments) >= 3:
            # Use the actual AI-generated segments (sorted by time)
            sorted_segs = sorted(script.segments, key=lambda s: s.start_time)
            body_segs = [s.text for s in sorted_segs if not s.is_hook]
            chunk = max(1, len(body_segs) // (count - 2))
            for i in range(count - 2):
                group = body_segs[i * chunk: (i + 1) * chunk]
                if group:
                    sections.append(" ".join(group))
        else:
            # Fallback: split body text into equal parts
            sentences = [s.strip() for s in body_text.replace(".", ". ").split(". ") if s.strip()]
            chunk = max(1, len(sentences) // (count - 2))
            for i in range(count - 2):
                group = sentences[i * chunk: (i + 1) * chunk]
                if group:
                    sections.append(" ".join(group))

        # 3. CTA — closing visual
        if script.cta:
            sections.append(script.cta.strip())

        # Ensure exactly `count` prompts
        while len(sections) < count:
            sections.append(script.full_text[:150])
        sections = sections[:count]

        return [
            (
                f"Cinematic vertical scene for a short-form video. "
                f"Depicted moment: {sec[:200]}. "
                f"Visual style: {suffix}. "
                f"Vertical 9:16, no text overlay, no watermark, photorealistic."
            )
            for sec in sections
        ]

    def _build_prompts(self, script: str, style: str, count: int) -> List[str]:
        """Build prompts from raw script text (simple chunk split)."""
        words = script.split()
        chunk_size = max(1, len(words) // count)
        suffix = STYLE_SUFFIX.get(style, "cinematic, high quality")

        return [
            (
                f"Cinematic vertical scene for a short-form video. "
                f"Depicted moment: {' '.join(words[i * chunk_size:(i + 1) * chunk_size])[:200].strip()}. "
                f"Visual style: {suffix}. "
                f"Vertical 9:16, no text overlay, no watermark, photorealistic."
            )
            for i in range(count)
        ]

