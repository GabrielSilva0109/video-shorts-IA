"""
B-Roll Service — fetches matching stock video clips from Pexels (primary)
and Pixabay (fallback).
"""
from __future__ import annotations
import asyncio
from pathlib import Path
from typing import List
import httpx
from loguru import logger
from app.config import settings


class BRollService:
    PEXELS_VIDEO_URL = "https://api.pexels.com/videos/search"
    PIXABAY_VIDEO_URL = "https://pixabay.com/api/videos/"

    async def fetch(
        self,
        keywords: List[str],
        count: int = 5,
        output_dir: Path = Path("./tmp"),
    ) -> List[Path]:
        """Download stock video clips or generate local backgrounds."""
        query = " ".join(keywords[:3])
        logger.info(f"Fetching B-roll: query='{query}' count={count}")

        video_urls: List[str] = []
        if settings.pexels_api_key:
            video_urls = await self._search_pexels(query, count)
        if not video_urls and settings.pixabay_api_key:
            video_urls = await self._search_pixabay(query, count)

        if video_urls:
            paths = await asyncio.gather(
                *[self._download(url, output_dir / f"broll_{i}.mp4")
                  for i, url in enumerate(video_urls[:count])]
            )
            return [p for p in paths if p is not None]

        # No API keys available — generate gradient backgrounds with FFmpeg
        logger.info("No B-roll API keys configured — generating gradient backgrounds")
        return await self._generate_local_clips(count, output_dir)

    async def _search_pexels(self, query: str, count: int) -> List[str]:
        if not settings.pexels_api_key:
            return []
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    self.PEXELS_VIDEO_URL,
                    params={"query": query, "per_page": count, "orientation": "portrait"},
                    headers={"Authorization": settings.pexels_api_key},
                )
                resp.raise_for_status()
                data = resp.json()
                urls = []
                for video in data.get("videos", []):
                    # Prefer HD vertical files
                    files = video.get("video_files", [])
                    hd = next(
                        (f for f in files if f.get("quality") == "hd"),
                        files[0] if files else None,
                    )
                    if hd:
                        urls.append(hd["link"])
                return urls
            except Exception as exc:
                logger.warning(f"Pexels search failed: {exc}")
                return []

    async def _search_pixabay(self, query: str, count: int) -> List[str]:
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    self.PIXABAY_VIDEO_URL,
                    params={
                        "key": settings.pixabay_api_key,
                        "q": query,
                        "per_page": count,
                        "video_type": "film",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                urls = []
                for hit in data.get("hits", []):
                    videos = hit.get("videos", {})
                    medium = videos.get("medium", {})
                    if medium.get("url"):
                        urls.append(medium["url"])
                return urls
            except Exception as exc:
                logger.warning(f"Pixabay search failed: {exc}")
                return []

    async def _generate_local_clips(self, count: int, output_dir: Path) -> List[Path]:
        """Create animated gradient background clips using FFmpeg (no API key needed)."""
        # Base colors + hue rotation speed for each slot (dark neon palette)
        configs = [
            ("4B006E", 8),   # deep purple
            ("001a4d", 12),  # navy blue
            ("0d2600", 7),   # deep green
            ("4d0000", 10),  # deep crimson
            ("1a1400", 9),   # deep gold
            ("001a1a", 11),  # deep teal
        ]
        paths: List[Path] = []
        for i in range(count):
            color, hue_speed = configs[i % len(configs)]
            dest = output_dir / f"broll_{i}.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=0x{color}:s=1080x1920:r=30",
                "-t", "6",
                "-vf", f"hue=h='t*{hue_speed}',eq=saturation=2.2:brightness=0.12:contrast=1.1",
                "-c:v", "libx264",
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                str(dest),
            ]
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await asyncio.wait_for(proc.wait(), timeout=30)
                if dest.exists():
                    paths.append(dest)
            except Exception as exc:
                logger.warning(f"FFmpeg background generation failed: {exc}")
        return paths

    @staticmethod
    async def _download(url: str, dest: Path) -> Path | None:
        try:
            async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                dest.write_bytes(resp.content)
                return dest
        except Exception as exc:
            logger.warning(f"Failed to download {url}: {exc}")
            return None
