from fastapi import APIRouter, HTTPException

from app.models.schemas import ImagerGenerateRequest, ImagerGenerateResponse
from app.services.flux_image_service import FluxImageService

router = APIRouter()
service = FluxImageService()


@router.post(
    "/generate",
    responses={500: {"description": "Failed to generate image"}},
)
async def generate_image(req: ImagerGenerateRequest) -> ImagerGenerateResponse:
    try:
        return await service.generate(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc