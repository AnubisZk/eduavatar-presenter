"""Final FFmpeg render route."""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.video_service import render_final_video


router = APIRouter(prefix="/render", tags=["render"])


class RenderRequest(BaseModel):
    """Request body for composing slides, avatar clips, audio, and subtitles."""

    project_id: str
    slide_paths: List[str]
    audio_files: List[str]
    avatar_videos: List[str]
    narration_sections: List[str]
    include_subtitles: bool = True


@router.post("/final")
def render_final_route(payload: RenderRequest):
    """Render the final presentation MP4."""
    try:
        final_path = render_final_video(
            project_id=payload.project_id,
            slide_paths=payload.slide_paths,
            audio_files=payload.audio_files,
            avatar_videos=payload.avatar_videos,
            narration_sections=payload.narration_sections,
            include_subtitles=payload.include_subtitles,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "FFmpeg is required to render the final MP4. Install it with "
                "`brew install ffmpeg`, then restart the backend."
            ),
        ) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Final render failed: {error}") from error
    return {"project_id": payload.project_id, "status": "rendered", "output_path": final_path}
