"""
Hook generator — generates viral hook variations using AI.
"""
from __future__ import annotations
import asyncio
import json
import os
from openai import AsyncOpenAI


HOOK_FORMATS = [
    "Question hook: start with a provocative question",
    "Shocking stat hook: lead with a surprising number or fact",
    "Controversy hook: make a bold controversial claim",
    "Story hook: start mid-story for instant engagement",
    "Secret hook: tease revealing insider information",
]


async def generate_hooks(
    topic: str,
    count: int = 5,
    api_key: str | None = None,
    model: str = "gpt-4o",
) -> list[str]:
    key = api_key or os.getenv("OPENAI_API_KEY", "")
    client = AsyncOpenAI(api_key=key)

    prompt = f"""Generate {count} viral TikTok hooks for the topic: "{topic}"

Each hook must:
- Be under 15 words
- Create instant curiosity or shock
- Work for the first 3 seconds of a video

Return JSON: {{"hooks": ["hook1", "hook2", ...]}}"""

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content or "{}")
    return data.get("hooks", [])


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("topic")
    p.add_argument("--count", type=int, default=5)
    args = p.parse_args()

    hooks = asyncio.run(generate_hooks(args.topic, args.count))
    for i, hook in enumerate(hooks, 1):
        print(f"{i}. {hook}")
