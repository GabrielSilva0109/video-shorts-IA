"""
Hashtag generator — generates platform-specific hashtags using AI.
"""
from __future__ import annotations
import asyncio
import json
import os
from openai import AsyncOpenAI


async def generate_hashtags(
    topic: str,
    platform: str = "tiktok",
    count: int = 20,
    api_key: str | None = None,
) -> list[str]:
    key = api_key or os.getenv("OPENAI_API_KEY", "")
    client = AsyncOpenAI(api_key=key)

    prompt = f"""Generate {count} viral {platform} hashtags for: "{topic}"

Mix of:
- Niche specific tags (5-10k-100k views range)  
- Mid-range tags (100k-1M views range)
- Trending broad tags (1M+ views range)

Return JSON: {{"hashtags": ["#tag1", "#tag2", ...]}}"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content or "{}")
    return data.get("hashtags", [])


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("topic")
    p.add_argument("--platform", default="tiktok")
    p.add_argument("--count", type=int, default=20)
    args = p.parse_args()

    tags = asyncio.run(generate_hashtags(args.topic, args.platform, args.count))
    print(" ".join(tags))
