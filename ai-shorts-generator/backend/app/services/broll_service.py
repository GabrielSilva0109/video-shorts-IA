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
        """Download stock video clips matching the keywords."""
        query = " ".join(keywords[:3])
        logger.info(f"Fetching B-roll: query='{query}' count={count}")

        video_urls = await self._search_pexels(query, count)
        if not video_urls and settings.pixabay_api_key:
            video_urls = await self._search_pixabay(query, count)

        if not video_urls:
            logger.warning("No B-roll found — using blank clip fallback")
            return []

        paths = await asyncio.gather(
            *[self._download(url, output_dir / f"broll_{i}.mp4")
              for i, url in enumerate(video_urls[:count])]
        )
        return [p for p in paths if p is not None]

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
