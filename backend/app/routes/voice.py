"""Voice generation route backed by the configured TTS service."""

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.tts_service import ScriptSection, generate_voice


router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceRequest(BaseModel):
    """Request body for slide narration generation."""

    project_id: str
    script_sections: List[ScriptSection]
    target_language: str
    voice_sample_path: str
    provider: str | None = None


@router.post("/generate")
def generate_voice_route(payload: VoiceRequest):
    """Generate one audio file per slide narration section."""
    audio_files = generate_voice(
        project_id=payload.project_id,
        script_sections=payload.script_sections,
        target_language=payload.target_language,
        voice_sample_path=payload.voice_sample_path,
        provider_name=payload.provider,
    )
    return {
        "project_id": payload.project_id,
        "status": "voice_generated",
        "provider": audio_files[0]["provider"] if audio_files else payload.provider,
        "audio_files": audio_files,
    }
