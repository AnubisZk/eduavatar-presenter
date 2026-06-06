"""Consent persistence for ethical avatar and voice use."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from pydantic import BaseModel

from app.services.storage_service import STORAGE_DIR


class ConsentPayload(BaseModel):
    """Validated consent data collected before uploads are accepted."""

    user_name: str
    image_permission: bool
    voice_permission: bool
    purpose_acknowledgement: bool
    misuse_acknowledgement: bool
    uploaded_file_names: Dict[str, str]


def save_consent_record(project_id: str, consent: ConsentPayload) -> Path:
    """Write a JSON consent record into uploads/{project_id}/consent.json."""
    project_dir = STORAGE_DIR / "uploads" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    consent_path = project_dir / "consent.json"
    record = {
        "project_id": project_id,
        "user_name": consent.user_name,
        "date_time": datetime.now(timezone.utc).isoformat(),
        "consent_checkboxes": {
            "image_permission": consent.image_permission,
            "voice_permission": consent.voice_permission,
            "purpose_acknowledgement": consent.purpose_acknowledgement,
            "misuse_acknowledgement": consent.misuse_acknowledgement,
        },
        "uploaded_file_names": consent.uploaded_file_names,
    }
    consent_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return consent_path
