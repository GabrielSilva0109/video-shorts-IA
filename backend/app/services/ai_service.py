"""AI Service — wraps OpenAI / Groq / Ollama for script, title,
description and hashtag generation."""
from __future__ import annotations
import json
import random
from typing import Optional
from openai import AsyncOpenAI
from loguru import logger
from app.config import settings
from app.models.schemas import (
    GeneratedScript,
    ScriptSegment,
    VideoStyle,
    AITitleSuggestions,
    AIDescriptionResult,
)

STYLE_GUIDES_EN: dict[str, str] = {
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

STYLE_GUIDES_PT: dict[str, str] = {
    "hormozi": (
        "Estilo Alex Hormozi: frases curtas e impactantes, afirmações ousadas, linguagem direta, "
        "use números e especificidades, prometa algo grande no gancho."
    ),
    "tiktok_story": (
        "Narrativa TikTok: prenda a atenção nos primeiros 2 segundos, "
        "crie tensão, use ganchos no final de cada frase."
    ),
    "finance": (
        "Short de finanças: comece com um fato chocante sobre dinheiro, explique de forma simples, "
        "termine com uma dica prática e acionável."
    ),
    "motivation": (
        "Edição motivacional: alta energia, inspire ação, use frases poderosas, "
        "aumente a intensidade ao longo do roteiro."
    ),
    "gaming": (
        "Short de gaming: estilo de comentário empolgante, use gírias de games, "
        "alta energia, referencie jogos e mecânicas populares."
    ),
    "luxury": (
        "Lifestyle de luxo: tom aspiracional, linguagem premium, pinte imagens vívidas "
        "de sucesso e abundância."
    ),
    "documentary": (
        "Short documentário: tom educacional, fatos fascinantes, "
        "narração autoritária, termine com uma reflexão instigante."
    ),
}

# Groq-compatible model (llama3, free at console.groq.com)
GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class AIService:
    def __init__(self) -> None:
        self._client: Optional[AsyncOpenAI] = None
        self._groq: Optional[AsyncOpenAI] = None

        if settings.openai_api_key:
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("AI: using OpenAI")
        elif settings.groq_api_key:
            self._groq = AsyncOpenAI(
                api_key=settings.groq_api_key,
                base_url=GROQ_BASE_URL,
            )
            logger.info("AI: using Groq (free)")
        else:
            logger.info("AI: no API key — using offline templates")

    # ── Shared AI call ───────────────────────
    async def _ai_complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.85,
        json_mode: bool = True,
    ) -> str | None:
        """Call best available AI client (OpenAI or Groq). Returns None if none configured."""
        client = self._client or self._groq
        if not client:
            return None
        model = settings.openai_model if self._client else settings.groq_model
        kwargs: dict = dict(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = await client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or "{}"
        except Exception as exc:
            logger.warning(f"AI call failed: {exc}")
            return None

    # ── Script generation ───────────────────────
    async def generate_script(
        self,
        prompt: str,
        style: VideoStyle | str,
        language: str = "pt",
    ) -> GeneratedScript:
        style_key = style.value if hasattr(style, "value") else str(style)
        is_pt = language.lower().startswith("pt")
        guides = STYLE_GUIDES_PT if is_pt else STYLE_GUIDES_EN
        style_guide = guides.get(style_key, guides["hormozi"])
        lang_name = "Português (pt-BR)" if is_pt else "English"

        system_prompt = f"""Você é um roteirista especialista em vídeos virais para redes sociais.
Idioma de saída: {lang_name}
Estilo: {style_guide}
TOPICO fornecido pelo usuário: \"{prompt}\"

Regras OBRIGATÓRIAS:
- O roteiro DEVE ser sobre o tópico acima, não algo genérico
- Use informações reais, específicas e concretas sobre o tópico
- Escreva EXATAMENTE no idioma {lang_name}
- O gancho deve mencionar o tópico diretamente

Retorne SOMENTE JSON válido neste formato:
{{
  "hook": "primeira frase (máx 15 palavras, para o scroll imediatamente)",
  "body": "conteúdo principal (60-120 palavras, específico sobre o tópico)",
  "cta": "chamada para ação (máx 15 palavras)",
  "full_text": "hook + body + cta combinados"
}}"""

        user_prompt = f"Crie um roteiro viral sobre: {prompt}"

        logger.info(f"Generating script | style={style_key} | lang={language}")

        raw: str | None = None
        if settings.enable_local_ai:
            raw = await self._local_generate(system_prompt, user_prompt)
        else:
            raw = await self._ai_complete(system_prompt, user_prompt)

        if not raw:
            raw = json.dumps(self._template_script(prompt, style_key, language))

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # AI returned non-JSON — fallback to template
            data = self._template_script(prompt, style_key, language)

        full_text: str = data.get("full_text", "")
        words = full_text.split()

        return GeneratedScript(
            hook=data.get("hook", ""),
            body=data.get("body", ""),
            cta=data.get("cta", ""),
            full_text=full_text,
            segments=self._build_segments(full_text),
            estimated_duration=round(len(words) / 2.5),
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
        raw = await self._ai_complete(system, user, temperature=0.7)
        return raw if raw else self._template_complete_json(system, user)

    # ── Offline / Template generation ────────
    @staticmethod
    def _template_script(prompt: str, style_key: str, language: str = "pt") -> dict:
        """Generate a varied script from templates — no API key required.
        Uses topic hash to pick between 3 variations so different prompts yield different results.
        """
        topic = prompt.strip().rstrip(".!?")
        is_pt = language.lower().startswith("pt")
        # Pick variation 0/1/2 based on topic content so same topic = same result
        v = abs(hash(topic.lower())) % 3

        if is_pt:
            HOOKS: dict[str, list[str]] = {
                "hormozi": [
                    f"A maioria das pessoas erra em {topic} por causa disso.",
                    f"Você está perdendo dinheiro em {topic} sem perceber.",
                    f"3 erros que destroem resultados em {topic}.",
                ],
                "tiktok_story": [
                    f"Eu quase desisti de {topic} até que isso aconteceu...",
                    f"Ninguém me avisou sobre isso antes de eu começar em {topic}.",
                    f"Em 30 dias mudei completamente minha visão sobre {topic}.",
                ],
                "finance": [
                    f"O custo real de ignorar {topic} vai te chocar.",
                    f"Como {topic} pode dobrar seu patrimônio em anos.",
                    f"A matemática de {topic} que ninguém te ensinou na escola.",
                ],
                "motivation": [
                    f"Seu potencial com {topic} é ilimitado — e aqui está a prova.",
                    f"Pare de esperar o momento perfeito para {topic}.",
                    f"A única coisa que separa você do sucesso em {topic}.",
                ],
                "gaming": [
                    f"Essa estratégia de {topic} está completamente quebrada agora.",
                    f"Por que os melhores jogadores dominam {topic} diferente.",
                    f"O segredo de {topic} que a maioria dos jogadores ignora.",
                ],
                "luxury": [
                    f"É assim que a elite aborda {topic}.",
                    f"Por que pessoas ricas investem em {topic} antes de tudo.",
                    f"O padrão ouro de {topic} que separa os melhores.",
                ],
                "documentary": [
                    f"A história não contada de {topic} é mais fascinante do que você imagina.",
                    f"O que a ciência descobriu recentemente sobre {topic}.",
                    f"Por que {topic} está mudando o mundo silenciosamente.",
                ],
            }
            BODIES: dict[str, list[str]] = {
                "hormozi": [
                    (f"Eles pulam os fundamentos e vão direto para táticas avançadas. "
                     f"Estudei {topic} a fundo: quem tem sucesso domina o básico primeiro. "
                     f"Construa sistemas, não dependências. Foco e execução consistente é tudo."),
                    (f"Em {topic}, 80% dos resultados vêm de 20% das ações. "
                     f"A maioria gasta tempo no que não importa. "
                     f"Mapeie o que realmente move o ponteiro e execute com obsessão."),
                    (f"Todo expert em {topic} cometeu os mesmos 3 erros no início. "
                     f"Erro 1: tentar tudo de uma vez. Erro 2: copiar sem adaptar. "
                     f"Erro 3: desistir antes de ver resultado. Evite esses e você já está à frente."),
                ],
                "tiktok_story": [
                    (f"Três meses atrás estava completamente travado com {topic}. "
                     f"Tentei todo tutorial, todo guia — zero resultado. "
                     f"Então encontrei um sistema diferente. Parei de copiar e comecei a criar. "
                     f"Em semanas os resultados apareceram mais rápido do que eu esperava."),
                    (f"Todo mundo fala que {topic} é difícil. E eu acreditei nisso por muito tempo. "
                     f"Até descobrir que o problema não era {topic} — era a abordagem. "
                     f"Uma mudança simples de mentalidade transformou tudo."),
                    (f"O dia em que decidi levar {topic} a sério mudou minha vida. "
                     f"Não foi fácil. Tive que aprender do zero, falhar várias vezes. "
                     f"Mas cada erro me ensinou algo que nenhum curso ensinaria."),
                ],
                "finance": [
                    (f"A maioria não percebe quanto dinheiro deixa na mesa ignorando {topic}. "
                     f"Pequenas ações consistentes se compõem ao longo do tempo. "
                     f"Independente do seu nível, dominar {topic} muda sua trajetória financeira."),
                    (f"Um investimento de R$100/mês em {topic} pode virar R$50.000 em 10 anos. "
                     f"O segredo é começar cedo e ser consistente. "
                     f"Quem espera o momento ideal nunca começa."),
                    (f"Ricos não ficam ricos apenas ganhando mais. "
                     f"Eles entendem como {topic} funciona e fazem o dinheiro trabalhar. "
                     f"É uma habilidade que qualquer um pode aprender."),
                ],
                "motivation": [
                    (f"Pare de deixar o medo te impedir em {topic}. "
                     f"Todo especialista foi iniciante. Toda história de sucesso começou com uma decisão. "
                     f"A diferença entre onde você está e onde quer estar é ação."),
                    (f"Você não precisa de condições perfeitas para começar em {topic}. "
                     f"Precisa de comprometimento. Precisa de consistência. "
                     f"O talento é superestimado — a disciplina constrói impérios."),
                    (f"Em {topic}, cada dia que você adia é um dia que alguém mais determinado avança. "
                     f"O desconforto é temporário. O arrependimento de não ter tentado é permanente. "
                     f"Sua escolha."),
                ],
                "gaming": [
                    (f"Tenho treinado {topic} por semanas e descobri algo insano. "
                     f"A maioria dos jogadores tá dormindo nisso. "
                     f"Quando você entende {topic} em alto nível, nunca mais volta para a abordagem antiga."),
                    (f"O meta de {topic} mudou e quem não se adaptou está ficando para trás. "
                     f"Os top players já sabem disso. "
                     f"Aqui está o que você precisa ajustar agora para subir de rank."),
                    (f"Existe uma diferença enorme entre jogar {topic} por diversão e jogar para vencer. "
                     f"Os melhores têm sistemas, rotinas e análise constante. "
                     f"Não é só mecânica — é mentalidade."),
                ],
                "luxury": [
                    (f"Existe uma razão pela qual o top 1% vê {topic} diferente de todos. "
                     f"Para eles, {topic} é investimento, não gasto. "
                     f"Os detalhes, a qualidade, a experiência — tudo importa nesse nível."),
                    (f"Pessoas que constroem legado entendem que {topic} não é sobre mostrar. "
                     f"É sobre padrão. É sobre quem você se torna no processo. "
                     f"O luxo real é ter tempo, liberdade e escolha."),
                    (f"Antes de chegar ao topo em {topic}, há uma jornada de refinamento. "
                     f"Cada detalhe elevado. Cada decisão intencional. "
                     f"Não é sorte — é um estilo de vida construído com propósito."),
                ],
                "documentary": [
                    (f"Por décadas, {topic} moldou nosso mundo de formas que a maioria nunca percebe. "
                     f"Pesquisadores descobriram que o que pensamos saber mal arranha a superfície. "
                     f"Quanto mais fundo você olha, mais complexo e bonito o quadro se torna."),
                    (f"A ciência por trás de {topic} revela padrões surpreendentes. "
                     f"O que parece simples esconde camadas de complexidade fascinantes. "
                     f"E cada nova descoberta levanta mais perguntas do que respostas."),
                    (f"Se você estudar a história de {topic}, vai encontrar um padrão claro. "
                     f"As maiores revoluções começaram em silêncio, ignoradas pela maioria. "
                     f"Hoje, {topic} está no início dessa mesma curva."),
                ],
            }
            CTAS: dict[str, list[str]] = {
                "hormozi": ["Siga para conteúdo direto ao ponto que gera resultado de verdade.", "Me segue para mais estratégias sem enrolação.", "Salva esse vídeo — você vai precisar disso."],
                "tiktok_story": ["Comenta 'QUERO MAIS' se quiser que eu mostre exatamente o que eu fiz.", "Segue para mais histórias reais sobre {topic}.", "Compartilha com quem precisa ouvir isso."],
                "finance": ["Siga para dicas diárias de dinheiro que realmente constroem riqueza.", "Salva esse vídeo antes de tomar sua próxima decisão financeira.", "Compartilha com alguém que precisa saber disso sobre {topic}."],
                "motivation": ["Siga para motivação diária que realmente move.", "Salva para quando precisar de um empurrão.", "Compartilha com quem está travado em {topic}."],
                "gaming": ["Dá um follow para mais estratégias e segredos de {topic}.", "Comenta sua dica de {topic} aqui embaixo.", "Salva para usar no seu próximo jogo."],
                "luxury": ["Siga para elevar seus padrões em {topic}.", "Compartilha com quem quer mais da vida.", "Me segue para mais conteúdo de alto nível."],
                "documentary": ["Siga para mais histórias fascinantes sobre o mundo.", "Comenta o que você não sabia sobre {topic}.", "Compartilha com alguém curioso sobre {topic}."],
            }
        else:
            HOOKS: dict[str, list[str]] = {
                "hormozi": [
                    f"Most people get {topic} wrong for this one reason.",
                    f"You're leaving money on the table with {topic} and don't know it.",
                    f"3 mistakes that kill results in {topic}.",
                ],
                "tiktok_story": [
                    f"I almost quit {topic} until this happened...",
                    f"Nobody warned me about this before I started {topic}.",
                    f"30 days completely changed how I see {topic}.",
                ],
                "finance": [
                    f"The real cost of ignoring {topic} will shock you.",
                    f"How {topic} can double your wealth in years.",
                    f"The math of {topic} nobody taught you in school.",
                ],
                "motivation": [
                    f"Your potential with {topic} is unlimited — here's proof.",
                    f"Stop waiting for the perfect moment to start {topic}.",
                    f"The only thing separating you from success in {topic}.",
                ],
                "gaming": [
                    f"This {topic} strategy is completely broken right now.",
                    f"Why top players dominate {topic} differently.",
                    f"The {topic} secret most players ignore.",
                ],
                "luxury": [
                    f"This is how the elite approach {topic}.",
                    f"Why wealthy people invest in {topic} first.",
                    f"The gold standard of {topic} that separates the best.",
                ],
                "documentary": [
                    f"The untold story of {topic} is more fascinating than you think.",
                    f"What science recently discovered about {topic}.",
                    f"Why {topic} is quietly changing the world.",
                ],
            }
            BODIES: dict[str, list[str]] = {
                "hormozi": [
                    (f"They skip fundamentals and jump to advanced tactics. "
                     f"I've studied {topic} deeply — those who succeed master basics first. "
                     f"Build systems, not dependencies. Focus and consistent execution is everything."),
                    (f"In {topic}, 80% of results come from 20% of actions. "
                     f"Most people waste time on what doesn't move the needle. "
                     f"Map what actually matters and execute with obsession."),
                    (f"Every expert in {topic} made the same 3 mistakes early on. "
                     f"Mistake 1: trying everything at once. Mistake 2: copying without adapting. "
                     f"Mistake 3: quitting before results come. Avoid these and you're already ahead."),
                ],
                "tiktok_story": [
                    (f"Three months ago I was completely stuck with {topic}. "
                     f"Tried every tutorial, every guide — zero results. "
                     f"Then I found a different system. Stopped copying and started creating. "
                     f"Within weeks results came faster than I ever expected."),
                    (f"Everyone says {topic} is hard. I believed that for too long. "
                     f"Until I realized the problem wasn't {topic} — it was my approach. "
                     f"One simple mindset shift transformed everything."),
                    (f"The day I decided to take {topic} seriously changed my life. "
                     f"It wasn't easy. I had to learn from scratch, fail multiple times. "
                     f"But each mistake taught me something no course ever could."),
                ],
                "finance": [
                    (f"Most people don't realize how much money they leave on the table ignoring {topic}. "
                     f"Small consistent actions compound over time. "
                     f"Whatever your level, mastering {topic} changes your financial trajectory."),
                    (f"Investing $100/month in {topic} can turn into $50,000 in 10 years. "
                     f"The secret is starting early and staying consistent. "
                     f"Those waiting for the ideal moment never start."),
                    (f"The wealthy don't get rich just by earning more. "
                     f"They understand how {topic} works and make money work for them. "
                     f"It's a skill anyone can learn."),
                ],
                "motivation": [
                    (f"Stop letting fear hold you back from {topic}. "
                     f"Every expert was once a beginner. Every success story started with one decision. "
                     f"The difference between where you are and where you want to be is action."),
                    (f"You don't need perfect conditions to start {topic}. "
                     f"You need commitment. You need consistency. "
                     f"Talent is overrated — discipline builds empires."),
                    (f"In {topic}, every day you delay is a day someone more determined advances. "
                     f"The discomfort is temporary. The regret of not trying is permanent. "
                     f"Your choice."),
                ],
                "gaming": [
                    (f"I've been grinding {topic} for weeks and found something insane. "
                     f"Most players are completely sleeping on this. "
                     f"Once you understand {topic} at a high level, you never go back."),
                    (f"The {topic} meta shifted and those who didn't adapt are falling behind. "
                     f"Top players already know this. "
                     f"Here's what you need to adjust now to rank up."),
                    (f"There's a huge difference between playing {topic} for fun and playing to win. "
                     f"The best have systems, routines, and constant analysis. "
                     f"It's not just mechanics — it's mindset."),
                ],
                "luxury": [
                    (f"There's a reason the top 1% see {topic} differently than everyone else. "
                     f"For them, {topic} is an investment, not an expense. "
                     f"The details, quality, experience — everything matters at this level."),
                    (f"People who build legacies understand that {topic} isn't about showing off. "
                     f"It's about standard. It's about who you become in the process. "
                     f"True luxury is time, freedom, and choice."),
                    (f"Before reaching the top in {topic}, there's a journey of refinement. "
                     f"Every detail elevated. Every decision intentional. "
                     f"Not luck — a lifestyle built with purpose."),
                ],
                "documentary": [
                    (f"For decades, {topic} has been shaping our world in ways most never notice. "
                     f"Researchers discovered what we think we know barely scratches the surface. "
                     f"The deeper you look, the more complex and beautiful the picture."),
                    (f"The science behind {topic} reveals surprising patterns. "
                     f"What seems simple hides layers of fascinating complexity. "
                     f"And every new discovery raises more questions than answers."),
                    (f"If you study the history of {topic}, you'll find a clear pattern. "
                     f"The biggest revolutions started quietly, ignored by most. "
                     f"Today, {topic} is at the beginning of that same curve."),
                ],
            }
            CTAS: dict[str, list[str]] = {
                "hormozi": ["Follow for no-BS content that actually moves the needle.", "Follow me for more straight-to-the-point strategies.", "Save this — you'll need it later."],
                "tiktok_story": ["Comment 'MORE' if you want me to break down what I did.", "Follow for more real stories about {topic}.", "Share this with someone who needs to hear it."],
                "finance": ["Follow for daily money tips that actually build wealth.", "Save this before your next financial decision.", "Share with someone who needs to know this about {topic}."],
                "motivation": ["Follow for daily motivation that actually moves you.", "Save for when you need a push.", "Share with someone stuck on {topic}."],
                "gaming": ["Drop a follow for more {topic} strategies and secrets.", "Comment your {topic} tip below.", "Save for your next game."],
                "luxury": ["Follow to elevate your standards in {topic}.", "Share with someone who wants more from life.", "Follow me for more high-level content."],
                "documentary": ["Follow for more fascinating stories about the world.", "Comment what you didn't know about {topic}.", "Share with someone curious about {topic}."],
            }

        hooks = HOOKS.get(style_key, HOOKS["hormozi"])
        bodies = BODIES.get(style_key, BODIES["hormozi"])
        ctas_raw = CTAS.get(style_key, CTAS["hormozi"])

        hook = hooks[v % len(hooks)]
        body = bodies[v % len(bodies)]
        cta = ctas_raw[v % len(ctas_raw)].replace("{topic}", topic)
        full_text = f"{hook} {body} {cta}"
        return {"hook": hook, "body": body, "cta": cta, "full_text": full_text}

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
