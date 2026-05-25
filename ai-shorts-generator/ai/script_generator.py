"""
Standalone script generator — can be used independently or imported.
"""
from __future__ import annotations
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from openai import AsyncOpenAI


HOOKS_TEMPLATES = [
    "The REAL reason {topic} is changing everything…",
    "{topic} just broke the internet — here's why",
    "Nobody is talking about this {topic} secret",
    "I spent 10 years learning {topic} — here's the shortcut",
    "Stop doing {topic} the wrong way",
    "This {topic} trick changed my life",
    "Warning: {topic} is not what you think",
    "The {topic} loophole that experts won't tell you",
]


async def generate_viral_script(
    topic: str,
    style: str = "hormozi",
    client: AsyncOpenAI | None = None,
    model: str = "gpt-4o",
) -> dict:
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        client = AsyncOpenAI(api_key=api_key)

    prompt = f"""You are an expert viral TikTok scriptwriter.
Write a {style}-style short video script about: {topic}

Requirements:
- Hook: First 3 seconds MUST stop the scroll (max 15 words)
- Body: 60-90 words. Bold claims. Short sentences. Numbers.
- CTA: Direct call to action (max 10 words)
- Total: ~45-60 seconds when spoken

Return valid JSON:
{{
  "hook": "...",
  "body": "...",
  "cta": "...",
  "full_text": "hook + body + cta"
}}"""

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content or "{}")


async def generate_hook_variations(topic: str, count: int = 5) -> list[str]:
    """Generate multiple hook variations for a topic."""
    hooks = []
    for template in HOOKS_TEMPLATES[:count]:
        hooks.append(template.replace("{topic}", topic))
    return hooks


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("topic", help="Video topic")
    parser.add_argument("--style", default="hormozi")
    args = parser.parse_args()

    result = asyncio.run(generate_viral_script(args.topic, args.style))
    print(json.dumps(result, indent=2))
