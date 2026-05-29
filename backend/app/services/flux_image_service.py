from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path

from loguru import logger

from app.config import settings
from app.models.schemas import ImagerGenerateRequest, ImagerGenerateResponse, ImagerModel


class FluxImageService:
    _pipelines: dict[ImagerModel, object] = {}
    _locks: dict[ImagerModel, asyncio.Lock] = {
        ImagerModel.flux_schnell: asyncio.Lock(),
        ImagerModel.flux_dev: asyncio.Lock(),
    }

    async def generate(self, req: ImagerGenerateRequest) -> ImagerGenerateResponse:
        output_dir = Path(settings.exports_dir) / "imager"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}.png"
        output_path = output_dir / filename
        chosen_seed = req.seed if req.seed is not None else None

        image = await asyncio.to_thread(self._run_generation, req)
        image.save(output_path)

        return ImagerGenerateResponse(
            image_url=f"/exports/imager/{filename}",
            image_path=str(output_path),
            model=req.model,
            width=req.width,
            height=req.height,
            seed=chosen_seed,
        )

    def _run_generation(self, req: ImagerGenerateRequest):
        pipeline = self._get_pipeline(req.model)
        generator = None

        kwargs = {
            "prompt": req.prompt,
            "height": req.height,
            "width": req.width,
        }

        if req.model == ImagerModel.flux_schnell:
            kwargs["num_inference_steps"] = 4
            kwargs["guidance_scale"] = 0.0
        else:
            kwargs["num_inference_steps"] = 20
            kwargs["guidance_scale"] = 3.5
            if req.seed is not None:
                import torch

                generator = torch.Generator("cpu").manual_seed(req.seed)
                kwargs["generator"] = generator

        logger.info(f"Generating FLUX image | model={req.model.value} | size={req.width}x{req.height}")
        result = pipeline(**kwargs)
        return result.images[0]

    def _get_pipeline(self, model: ImagerModel):
        cached = self._pipelines.get(model)
        if cached is not None:
            return cached

        lock = self._locks[model]
        if lock.locked():
            raise RuntimeError("FLUX model is loading. Try again in a moment.")

        return self._load_pipeline_blocking(model)

    def _load_pipeline_blocking(self, model: ImagerModel):
        cached = self._pipelines.get(model)
        if cached is not None:
            return cached

        try:
            import torch
            from diffusers import FluxPipeline
        except Exception as exc:
            raise RuntimeError(
                "FLUX import failed in the current backend runtime. "
                f"python={sys.executable}. "
                "Ensure diffusers, transformers, accelerate, torch and torchvision are installed in this exact environment. "
                f"Original error: {exc}"
            ) from exc

        model_id = {
            ImagerModel.flux_schnell: "black-forest-labs/FLUX.1-schnell",
            ImagerModel.flux_dev: "black-forest-labs/FLUX.1-dev",
        }[model]

        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        logger.info(f"Loading FLUX pipeline: {model_id}")
        try:
            pipe = FluxPipeline.from_pretrained(model_id, torch_dtype=dtype)
        except Exception as exc:
            msg = str(exc)
            if "gated repo" in msg.lower() or "401" in msg:
                raise RuntimeError(
                    "Access denied to FLUX model on Hugging Face (gated repo). "
                    "Request access to black-forest-labs/FLUX.1-schnell and/or FLUX.1-dev, "
                    "then authenticate in the backend environment (huggingface-cli login or HUGGINGFACE_HUB_TOKEN). "
                    f"python={sys.executable}."
                ) from exc
            raise RuntimeError(f"Failed to load FLUX model {model_id}: {exc}") from exc

        if torch.cuda.is_available():
            pipe.enable_model_cpu_offload()
        else:
            pipe.to("cpu")

        self._pipelines[model] = pipe
        return pipe