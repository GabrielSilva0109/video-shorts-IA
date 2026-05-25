"""
AI Service — wraps OpenAI (and optional Ollama) for script, title,
description and hashtag generation.
"""
from __future__ import annotations
import json
from typing import Optional
from openai import AsyncOpenAI
from fastapi import HTTPException
from loguru import logger
from app.config import settings
from app.models.schemas import (
    GeneratedScript,
    ScriptSegment,
    VideoStyle,
    AITitleSuggestions,
    AIDescriptionResult,
)

STYLE_GUIDES: dict[str, str] = {
    "hormozi": (
        "Alex Hormozi style: short punchy sentences, bold claims, direct address, "
        "use numbers and specifics, present a big promise in the hook."
    ),
    "tiktok_story": (
        "TikTok storytelling: hook the viewer in the first 2 seconds, "
        "build tension, use cliffhangers between sentences."
    ),
    "finance": (
        "Finance short: start with a shocking money fact, explain simply, "
        "end with an actionable tip."
    ),
    "motivation": (
        "Motivation edit: high energy, inspire action, use powerful quotes, "
        "escalate intensity throughout."
    ),
    "gaming": (
        "Gaming short: exciting gaming commentary style, use gaming slang, "
        "high energy, reference popular games."
    ),
    "luxury": (
        "Luxury lifestyle: aspirational tone, premium language, paint vivid "
        "imagery of success and abundance."
    ),
    "documentary": (
        "Documentary short: educational tone, fascinating facts, "
        "authoritative narration, end with a thought-provoking statement."
    ),
}


class AIService:
    def __init__(self) -> None:
        self._client: Optional[AsyncOpenAI] = None
        if settings.openai_api_key:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    # ── Script generation ────────────────────
    async def generate_script(
        self,
        prompt: str,
        style: VideoStyle | str,
        language: str = "en",
    ) -> GeneratedScript:
        style_key = style.value if hasattr(style, "value") else str(style)
        style_guide = STYLE_GUIDES.get(style_key, STYLE_GUIDES["hormozi"])

        system_prompt = f"""You are an expert viral short-video scriptwriter.
Style guide: {style_guide}
Language: {language}
Output ONLY valid JSON matching this schema:
{{
  "hook": "first sentence (max 15 words, must stop the scroll)",
  "body": "main content (60-120 words)",
  "cta": "call to action (max 15 words)",
  "full_text": "hook + body + cta combined"
}}"""

        user_prompt = f"Write a viral short video script about: {prompt}"

        logger.info(f"Generating script | style={style_key} | lang={language}")

        if settings.enable_local_ai:
            raw = await self._local_generate(system_prompt, user_prompt)
        elif not self._client:
            raw = json.dumps(self._template_script(prompt, style_key))
        else:
            response = await self._client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.85,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"

        data = json.loads(raw)
        full_text: str = data.get("full_text", "")
        words = full_text.split()

        return GeneratedScript(
            hook=data.get("hook", ""),
            body=data.get("body", ""),
            cta=data.get("cta", ""),
            full_text=full_text,
            segments=self._build_segments(full_text),
            estimated_duration=round(len(words) / 2.5),  # ~2.5 words/sec
            word_count=len(words),
        )

    # ── Title suggestions ────────────────────
    async def generate_titles(self, script: str) -> AITitleSuggestions:
        system_prompt = """Generate viral titles and hooks for a short video.
Output ONLY valid JSON:
{"titles": ["title1", "title2", "title3", "title4", "title5"],
 "hooks": ["hook1", "hook2", "hook3"]}"""

        raw = await self._complete(system_prompt, f"Script:\n{script}")
        data = json.loads(raw)
        return AITitleSuggestions(
            titles=data.get("titles", []),
            hooks=data.get("hooks", []),
        )

    # ── Description + hashtags ───────────────
    async def generate_description(
        self, script: str, platform: str = "tiktok"
    ) -> AIDescriptionResult:
        system_prompt = f"""Generate a {platform} video description, hashtags and keywords.
Output ONLY valid JSON:
{{"description": "...", "hashtags": ["#tag1", ...], "keywords": ["kw1", ...]}}"""

        raw = await self._complete(system_prompt, f"Script:\n{script}")
        data = json.loads(raw)
        return AIDescriptionResult(
            description=data.get("description", ""),
            hashtags=data.get("hashtags", []),
            keywords=data.get("keywords", []),
        )

    # ── Helpers ──────────────────────────────
    async def _complete(self, system: str, user: str) -> str:
        if settings.enable_local_ai:
            return await self._local_generate(system, user)
        if not self._client:
            return self._template_complete_json(system, user)
        response = await self._client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or "{}"

    # ── Offline / Template generation ────────
    @staticmethod
    def _template_script(prompt: str, style_key: str) -> dict:
        """Generate a script from templates — no API key required."""
        topic = prompt.strip().rstrip(".!?")
        SCRIPTS: dict[str, dict] = {
            "hormozi": {
                "hook": f"Most people fail at {topic} for one simple reason.",
                "body": (
                    f"They skip the fundamentals and jump straight to advanced tactics. "
                    f"I've studied {topic} closely and the pattern is always the same. "
                    f"The people who succeed master the basics first, then build repeatable systems. "
                    f"It's not complicated — it just requires the right focus and consistent execution."
                ),
                "cta": "Follow for more no-BS content that actually moves the needle.",
            },
            "tiktok_story": {
                "hook": f"I almost gave up on {topic} until this happened...",
                "body": (
                    f"Three months ago I was completely stuck with {topic} and nothing was working. "
                    f"I tried every tutorial, every guide — zero results. "
                    f"Then one day I noticed something that changed everything. "
                    f"I stopped doing what everyone else was doing and found my own system. "
                    f"Within weeks the results started coming in faster than I ever expected."
                ),
                "cta": "Comment 'MORE' if you want me to break down exactly what I did.",
            },
            "finance": {
                "hook": f"The real cost of ignoring {topic} will shock you.",
                "body": (
                    f"Most people don't realize how much money they're leaving on the table with {topic}. "
                    f"The math is simple: small consistent actions compound over time. "
                    f"Whether you're just starting or already deep into {topic}, "
                    f"understanding the fundamentals can completely change your financial trajectory."
                ),
                "cta": "Follow for daily money tips that actually build wealth.",
            },
            "motivation": {
                "hook": f"Your potential with {topic} is unlimited — here's proof.",
                "body": (
                    f"Stop letting fear hold you back from {topic}. "
                    f"Every expert was once a beginner. Every success story started with a single decision. "
                    f"The only difference between where you are and where you want to be is action. "
                    f"Take one step toward {topic} today. Then another tomorrow. "
                    f"Consistency beats talent every single time."
                ),
                "cta": "Follow for daily motivation to keep pushing forward.",
            },
            "gaming": {
                "hook": f"This {topic} strategy is absolutely broken right now.",
                "body": (
                    f"I've been grinding {topic} for weeks and found something insane. "
                    f"Most players are completely sleeping on this. "
                    f"Once you understand how {topic} actually works at a high level, "
                    f"you'll never go back to your old approach. "
                    f"This is game-changing info that top players don't want you to know."
                ),
                "cta": "Drop a follow for more broken strats and gaming secrets.",
            },
            "luxury": {
                "hook": f"This is how the elite approach {topic}.",
                "body": (
                    f"There's a reason the top 1% see {topic} differently than everyone else. "
                    f"While most people settle for average, those who operate at the highest level "
                    f"understand that {topic} is an investment, not an expense. "
                    f"The details, the quality, the experience — everything matters at this level."
                ),
                "cta": "Follow to elevate your standards and live at a higher level.",
            },
            "documentary": {
                "hook": f"The untold story of {topic} is more fascinating than you think.",
                "body": (
                    f"For decades, {topic} has been shaping our world in ways most people never notice. "
                    f"Researchers who study {topic} have discovered that what we think we know "
                    f"barely scratches the surface. "
                    f"The deeper you look, the more complex and beautiful the picture becomes."
                ),
                "cta": "Follow for more fascinating stories about the world around us.",
            },
        }
        data = SCRIPTS.get(style_key, SCRIPTS["hormozi"])
        full_text = f"{data['hook']} {data['body']} {data['cta']}"
        return {**data, "full_text": full_text}

    @staticmethod
    def _template_complete_json(system: str, user: str) -> str:
        """Return template-based JSON for titles/descriptions without any API."""
        script_text = user.replace("Script:\n", "").strip()
        first_sentence = (script_text.split(".")[0] + ".")[:80]
        words = [
            w.lower().strip(".,!?\"'")
            for w in script_text.split()
            if len(w) > 4 and w.isalpha()
        ][:12]

        if '"titles"' in system:
            return json.dumps({
                "titles": [
                    "Nobody talks about this",
                    "This changed everything for me",
                    "Watch this before you do anything else",
                    "The truth nobody tells you",
                    "Stop wasting time, do this instead",
                ],
                "hooks": [
                    first_sentence,
                    "Wait until you hear what happens next...",
                    "This is the most important thing you'll see today.",
                ],
            })

        if '"hashtags"' in system:
            hashtags = [f"#{w}" for w in words[:5]] + [
                "#shorts", "#viral", "#fyp", "#trending", "#reels"
            ]
            return json.dumps({
                "description": script_text[:200] + ("..." if len(script_text) > 200 else ""),
                "hashtags": hashtags[:10],
                "keywords": words[:8],
            })

        return "{}"

    async def _local_generate(self, system: str, user: str) -> str:
        """Fallback: use Ollama local inference."""
        import httpx

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.ollama_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "format": "json",
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    @staticmethod
    def _build_segments(text: str) -> list[ScriptSegment]:
        """Split full text into timed segments (approx. 2.5 words/sec)."""
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        segments: list[ScriptSegment] = []
        current_time = 0.0
        for i, sentence in enumerate(sentences):
            word_count = len(sentence.split())
            duration = word_count / 2.5
            segments.append(
                ScriptSegment(
                    text=sentence + ".",
                    start_time=round(current_time, 2),
                    end_time=round(current_time + duration, 2),
                    is_hook=(i == 0),
                )
            )
            current_time += duration
        return segments
