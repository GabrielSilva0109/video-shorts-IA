"""
Template Service — loads video templates from JSON files.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import List
from loguru import logger

TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent / "templates"


class TemplateService:
    def list_templates(self) -> List[dict]:
        templates: List[dict] = []
        if not TEMPLATES_DIR.exists():
            logger.warning(f"Templates directory not found: {TEMPLATES_DIR}")
            return []

        for path in sorted(TEMPLATES_DIR.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                templates.append(data)
            except Exception as exc:
                logger.warning(f"Failed to load template {path.name}: {exc}")

        return templates
