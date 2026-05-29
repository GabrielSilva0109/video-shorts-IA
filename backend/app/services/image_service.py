"""
Image Service — generates 5 scene images via Pollinations.ai (primary, free),
DALL-E 3, or Pillow-based scene cards (offline fallback).
"""
from __future__ import annotations
import asyncio
import os
import subprocess
import textwrap
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
    _active_projects: set[str] = set()
    _active_lock = asyncio.Lock()

    async def generate_and_save(
        self,
        project_id: str,
        script: "GeneratedScript",
        style: str,
        count: int = 3,
    ) -> None:
        """Generate images strictly one-by-one and persist each completed image."""
        output_dir = Path(settings.exports_dir) / project_id / "images"

        async with self._active_lock:
            if project_id in self._active_projects:
                logger.info(f"[{project_id}] Image generation already in progress — skipping duplicate task")
                return
            self._active_projects.add(project_id)

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            prompts = self._prompts_from_script(script, style, count)
            paths: List[str] = []

            # Clear previous list first so UI starts from a clean state
            store.update_project(project_id, generated_images=[])

            for i, prompt in enumerate(prompts[:count]):
                path = await self._generate_single_image(prompt, output_dir, i, count, style)
                if path:
                    paths.append(path)
                    # Persist after each image so frontend can show progress immediately
                    store.update_project(project_id, generated_images=list(paths))
                # tiny pacing helps avoid provider burst/rate penalties
                await asyncio.sleep(0.9)

            logger.success(f"[{project_id}] {len(paths)} scene images saved")
        except Exception as exc:
            logger.error(f"[{project_id}] Image generation failed: {exc}")
        finally:
            async with self._active_lock:
                self._active_projects.discard(project_id)

    async def _generate_single_image(
        self,
        prompt: str,
        output_dir: Path,
        index: int,
        total: int,
        style: str,
    ) -> str | None:
        """Generate one real image per slot with fast fallback to local artwork."""
        out_jpg = output_dir / f"img_{index}.jpg"

        try:
            generated = await asyncio.wait_for(
                self._pollinations_one(prompt, out_jpg, index),
                timeout=18,
            )
            if generated.exists() and generated.stat().st_size > 10_000:
                return str(generated)
            generated.unlink(missing_ok=True)
        except Exception as exc:
            logger.warning(f"[Image {index}] Pollinations failed, using local fallback: {exc}")

        if settings.openai_api_key:
            try:
                from openai import AsyncOpenAI

                out_png = output_dir / f"img_{index}.png"
                client = AsyncOpenAI(api_key=settings.openai_api_key)
                generated = await asyncio.wait_for(
                    self._dalle_one(client, prompt, out_png, index),
                    timeout=45,
                )
                if generated.exists() and generated.stat().st_size > 10_000:
                    return str(generated)
                generated.unlink(missing_ok=True)
            except Exception as exc:
                logger.warning(f"[Image {index}] DALL-E failed, using local fallback: {exc}")

        self._draw_scene_card(prompt, out_jpg, index, total, style)
        return str(out_jpg)

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
        return await self._run_pipeline(prompts, output_dir, count, style)

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
        return await self._run_pipeline(prompts, output_dir, count, style)

    async def _run_pipeline(
        self, prompts: List[str], output_dir: Path, count: int, style: str = ""
    ) -> List[str]:
        """Generate scene cards with Pillow first (always works), then try to
        upgrade individual slots with Pollinations/DALL-E if available."""
        results: dict[int, str] = {}

        # 1. Pillow scene cards — instant, fully offline, always succeeds
        for i, prompt in enumerate(prompts[:count]):
            try:
                out = output_dir / f"img_{i}.jpg"
                self._draw_scene_card(prompt, out, i, count, style)
                results[i] = str(out)
            except Exception as exc:
                logger.warning(f"Pillow card {i} failed: {exc}")

        logger.info(f"Pillow: {len(results)}/{count} scene cards generated")

        # 2. Pollinations upgrade — replace slots with real AI images when it works
        for i, prompt in enumerate(prompts[:count]):
            try:
                p = await self._pollinations_one(prompt, output_dir / f"img_{i}.jpg", i)
                if p.stat().st_size > 1024:
                    results[i] = str(p)
                else:
                    p.unlink(missing_ok=True)
            except Exception:
                pass  # silently keep the Pillow card
            await asyncio.sleep(0.3)

        # 3. DALL-E upgrade for any slot that still has only a Pillow card
        if settings.openai_api_key:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            for i in range(count):
                try:
                    p = await self._dalle_one(client, prompts[i], output_dir / f"img_{i}.png", i)
                    results[i] = str(p)
                except Exception:
                    pass

        return [results[i] for i in range(count) if i in results]

    # ── Pollinations.ai ───────────────────────
    async def _pollinations_one(self, prompt: str, output_path: Path, index: int) -> Path:
        from urllib.parse import quote

        compact_prompt = prompt[:220]
        encoded = quote(compact_prompt)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width=768&height=1365&seed={index * 42}"
        )

        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=20) as http:
                    resp = await http.get(url, follow_redirects=True)
                    resp.raise_for_status()
                    output_path.write_bytes(resp.content)
                logger.info(f"[Pollinations {index}] saved → {output_path.name}")
                return output_path
            except Exception as exc:
                last_exc = exc
                # If provider rejects long prompt/budget, retry with a simpler prompt.
                if "402" in str(exc) and attempt == 0:
                    simple_prompt = quote(compact_prompt.split(". Visual style")[0][:120])
                    url = (
                        f"https://image.pollinations.ai/prompt/{simple_prompt}"
                        f"?width=768&height=1365&seed={index * 137 + 7}"
                    )
                await asyncio.sleep(0.8 + (attempt * 0.6))

        assert last_exc is not None
        raise last_exc

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

    # ── Pillow scene cards (offline) ─────────
    _CARD_PALETTE: dict[str, tuple] = {
        "hormozi":           ((15, 15, 15),   (160, 15, 15)),
        "tiktok_story":      ((180, 0, 100),  (60, 0, 120)),
        "finance":           ((10, 35, 80),   (0, 110, 100)),
        "motivation":        ((60, 0, 120),   (15, 15, 40)),
        "gaming":            ((5, 0, 40),     (0, 180, 220)),
        "luxury":            ((18, 18, 18),   (130, 95, 10)),
        "documentary":       ((20, 30, 55),   (50, 100, 150)),
    }

    def _draw_scene_card(
        self,
        prompt: str,
        output_path: Path,
        index: int,
        total: int,
        style: str,
    ) -> None:
        """Draw a 1080×1920 scene card with gradient + script text via Pillow."""
        from PIL import Image, ImageDraw, ImageFont

        # Extract readable text from the prompt string
        text = prompt
        if "Depicted moment:" in text:
            text = text.split("Depicted moment:")[1].split(". Visual style")[0].strip()
        text = text.rstrip(".")[:220]

        # Pick gradient colors
        c0, c1 = self._CARD_PALETTE.get(style, ((20, 20, 50), (5, 5, 20)))

        W, H = 1080, 1920
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)

        # Vertical gradient
        for y in range(H):
            t = y / H
            draw.line(
                [(0, y), (W, y)],
                fill=(
                    int(c0[0] + (c1[0] - c0[0]) * t),
                    int(c0[1] + (c1[1] - c0[1]) * t),
                    int(c0[2] + (c1[2] - c0[2]) * t),
                ),
            )

        # Subtle vignette overlay
        for r in range(min(W, H) // 2, 0, -8):
            alpha = int(80 * (1 - r / (min(W, H) / 2)))
            draw.ellipse(
                [(W // 2 - r, H // 2 - r), (W // 2 + r, H // 2 + r)],
                outline=(0, 0, 0, alpha),
            )

        # Fonts — try Windows system fonts, fall back gracefully
        def _font(name: str, size: int):
            candidates = [
                f"C:/Windows/Fonts/{name}",
                f"/usr/share/fonts/truetype/dejavu/{name}",
            ]
            for path in candidates:
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        font_body = _font("arialbd.ttf", 44)
        font_label = _font("arial.ttf", 44)

        # Draw a short scene hint instead of a full centered caption.
        lines = textwrap.wrap(text, width=24)[:2]
        line_h = 60
        block_h = len(lines) * line_h
        y_pos = H - 320 - block_h

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font_body)
            tw = bbox[2] - bbox[0]
            x = 70
            draw.rounded_rectangle(
                [(50, y_pos - 20), (min(W - 50, x + tw + 40), y_pos + 54)],
                radius=26,
                fill=(0, 0, 0, 120),
            )
            draw.text((x, y_pos), line, fill=(255, 255, 255), font=font_body)
            y_pos += line_h

        # Scene indicator badge (bottom center)
        badge = f"{index + 1} / {total}"
        bbox = draw.textbbox((0, 0), badge, font=font_label)
        bw = bbox[2] - bbox[0]
        bx = (W - bw) // 2
        draw.rounded_rectangle(
            [(bx - 24, H - 130), (bx + bw + 24, H - 60)],
            radius=30,
            fill=(255, 255, 255, 40),
        )
        draw.text((bx + 2, H - 128), badge, fill=(0, 0, 0), font=font_label)
        draw.text((bx, H - 130), badge, fill=(255, 255, 255), font=font_label)

        img.save(str(output_path), "JPEG", quality=92)
        logger.info(f"[Pillow {index}] scene card saved → {output_path.name}")

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
        self, script: "GeneratedScript", style: str, count: int = 3
    ) -> List[str]:
        """Build visual prompts: hook (início) / body segments / cta (fim)."""
        suffix = STYLE_SUFFIX.get(style, "cinematic, high quality")

        sections: List[str] = []

        # Sempre começa com o hook
        if script.hook:
            sections.append(script.hook.strip())

        # Corpo dividido em (count - 2) partes, mínimo 1
        body_parts = count - 2
        if body_parts > 0:
            body_text = script.body or script.full_text
            sentences = [s.strip() for s in body_text.replace(". ", ".|").split("|") if s.strip()]
            chunk = max(1, len(sentences) // body_parts)
            for i in range(body_parts):
                group = sentences[i * chunk: (i + 1) * chunk]
                sections.append(" ".join(group) if group else body_text[:150])

        # Sempre termina com o CTA
        if script.cta:
            sections.append(script.cta.strip())

        # Garante exatamente `count` seções
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

