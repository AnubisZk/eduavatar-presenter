"""Presentation script and slide processing routes."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.presentation_service import build_script_sections


router = APIRouter(prefix="/presentation", tags=["presentation"])


class ScriptRequest(BaseModel):
    """Request body for dividing narration into slide-level sections."""

    project_id: str
    original_script: str = Field(..., min_length=1)
    target_language: str = Field(default="English")
    slide_count: int = Field(default=1, ge=1)


@router.post("/script")
def create_script_sections(payload: ScriptRequest):
    """Split or generate a script outline and estimate slide durations."""
    sections = build_script_sections(
        project_id=payload.project_id,
        original_script=payload.original_script,
        target_language=payload.target_language,
        slide_count=payload.slide_count,
    )
    return {
        "project_id": payload.project_id,
        "target_language": payload.target_language,
        "sections": sections,
    }
