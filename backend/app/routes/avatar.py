"""Avatar video generation route."""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.avatar_service import generate_avatar_video, selected_avatar_provider_name


router = APIRouter(prefix="/avatar", tags=["avatar"])


class AvatarRequest(BaseModel):
    """Request body for lip-synced talking avatar generation."""

    project_id: str
    avatar_source_path: str
    audio_files: List[str]
    provider: str | None = None


@router.post("/generate")
def generate_avatar_route(payload: AvatarRequest):
    """Generate avatar clips for each audio file using the configured provider."""
    try:
        clips = [
            generate_avatar_video(
                payload.project_id,
                payload.avatar_source_path,
                audio_path,
                provider_name=payload.provider,
            )
            for audio_path in payload.audio_files
        ]
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Avatar generation failed: {error}") from error
    return {
        "project_id": payload.project_id,
        "status": "avatar_generated",
        "provider": payload.provider or selected_avatar_provider_name(),
        "avatar_videos": clips,
    }
