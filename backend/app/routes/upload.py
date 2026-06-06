"""Upload and consent endpoints."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.consent_service import ConsentPayload, save_consent_record
from app.services.presentation_service import process_presentation
from app.services.storage_service import save_upload, validate_extension


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("")
async def upload_project_files(
    user_name: str = Form(...),
    image_permission: bool = Form(...),
    voice_permission: bool = Form(...),
    purpose_acknowledgement: bool = Form(...),
    misuse_acknowledgement: bool = Form(...),
    avatar_file: UploadFile = File(...),
    voice_file: UploadFile = File(...),
    presentation_file: UploadFile = File(...),
):
    """Accept consent plus avatar, voice, and presentation files in one project upload."""
    if not all(
        [
            image_permission,
            voice_permission,
            purpose_acknowledgement,
            misuse_acknowledgement,
        ]
    ):
        raise HTTPException(status_code=400, detail="All consent confirmations are required.")

    validate_extension(avatar_file.filename, {"jpg", "jpeg", "png", "mp4", "mov"})
    validate_extension(voice_file.filename, {"wav", "mp3"})
    validate_extension(presentation_file.filename, {"pdf", "pptx"})

    project_id, avatar_path = await save_upload(avatar_file)
    _, voice_path = await save_upload(voice_file, project_id=project_id)
    _, presentation_path = await save_upload(presentation_file, project_id=project_id)

    consent = ConsentPayload(
        user_name=user_name,
        image_permission=image_permission,
        voice_permission=voice_permission,
        purpose_acknowledgement=purpose_acknowledgement,
        misuse_acknowledgement=misuse_acknowledgement,
        uploaded_file_names={
            "avatar": avatar_file.filename or "",
            "voice": voice_file.filename or "",
            "presentation": presentation_file.filename or "",
        },
    )
    consent_path = save_consent_record(project_id, consent)
    slides = process_presentation(project_id, presentation_path)

    return {
        "project_id": project_id,
        "status": "uploaded",
        "file_paths": {
            "avatar": str(avatar_path),
            "voice": str(voice_path),
            "presentation": str(presentation_path),
            "consent": str(consent_path),
        },
        "slides": slides,
    }


@router.post("/{project_id}/file")
async def upload_single_file(
    project_id: str,
    file_type: str = Form(...),
    file: UploadFile = File(...),
):
    """Optional modular upload endpoint for clients that upload one asset at a time."""
    allowed = {
        "avatar": {"jpg", "jpeg", "png", "mp4", "mov"},
        "voice": {"wav", "mp3"},
        "presentation": {"pdf", "pptx"},
    }
    if file_type not in allowed:
        raise HTTPException(status_code=400, detail="file_type must be avatar, voice, or presentation.")
    validate_extension(file.filename, allowed[file_type])
    _, stored_path = await save_upload(file, project_id=project_id)
    response = {"project_id": project_id, "status": "uploaded", "file_path": str(stored_path)}
    if file_type == "presentation":
        response["slides"] = process_presentation(project_id, stored_path)
    return response
