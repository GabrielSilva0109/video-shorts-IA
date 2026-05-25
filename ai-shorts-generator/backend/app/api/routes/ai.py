from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ScriptRequest,
    TitleRequest,
    DescriptionRequest,
    GeneratedScript,
    AITitleSuggestions,
    AIDescriptionResult,
)
from app.services.ai_service import AIService

router = APIRouter()
ai_service = AIService()


@router.post("/script", response_model=GeneratedScript)
async def generate_script(req: ScriptRequest) -> GeneratedScript:
    """Generate a viral short-form script from a topic/prompt."""
    try:
        return await ai_service.generate_script(req.prompt, req.style, req.language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/titles", response_model=AITitleSuggestions)
async def generate_titles(req: TitleRequest) -> AITitleSuggestions:
    """Generate title and hook suggestions for a script."""
    try:
        return await ai_service.generate_titles(req.script)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/description", response_model=AIDescriptionResult)
async def generate_description(req: DescriptionRequest) -> AIDescriptionResult:
    """Generate description, hashtags and keywords for the video."""
    try:
        return await ai_service.generate_description(req.script, req.platform)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
