from fastapi import APIRouter
from app.services.template_service import TemplateService
from app.models.schemas import VideoTemplate  # type: ignore[attr-defined]

router = APIRouter()
template_service = TemplateService()


@router.get("", response_model=list[dict])
async def list_templates() -> list[dict]:
    return template_service.list_templates()
