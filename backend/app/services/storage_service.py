"""Shared storage helpers for uploads and generated files."""

from pathlib import Path
from typing import Optional, Set, Tuple
from uuid import uuid4

from fastapi import HTTPException, UploadFile


# All generated paths are anchored to app/storage for predictable local development.
APP_DIR = Path(__file__).resolve().parents[1]
STORAGE_DIR = APP_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"


def ensure_storage_dirs() -> None:
    """Create storage directories if they do not exist."""
    for directory in ["uploads", "slides", "audio", "avatars", "outputs"]:
        (STORAGE_DIR / directory).mkdir(parents=True, exist_ok=True)


def validate_extension(filename: Optional[str], allowed_extensions: Set[str]) -> None:
    """Validate a filename extension against an allowed extension set."""
    if not filename or "." not in filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have an extension.")
    extension = filename.rsplit(".", 1)[-1].lower()
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed}.")


def safe_filename(filename: str) -> str:
    """Keep uploaded filenames readable while removing risky path characters."""
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in filename)


async def save_upload(file: UploadFile, project_id: Optional[str] = None) -> Tuple[str, Path]:
    """Save an UploadFile into uploads/{project_id}/ and return the project id plus path."""
    ensure_storage_dirs()
    project_id = project_id or uuid4().hex
    project_dir = UPLOAD_DIR / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    stored_path = project_dir / safe_filename(file.filename or f"upload_{uuid4().hex}")
    content = await file.read()
    stored_path.write_bytes(content)
    return project_id, stored_path


def storage_url(path: Path) -> str:
    """Convert an absolute storage path into a frontend-accessible /storage URL."""
    relative = path.resolve().relative_to(STORAGE_DIR.resolve())
    return f"/storage/{relative.as_posix()}"
