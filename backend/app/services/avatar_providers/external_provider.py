"""Scaffolds for future real talking-avatar model integrations."""

import os

from app.services.avatar_providers.base import AvatarProvider


class NotConfiguredAvatarProvider(AvatarProvider):
    """Return a clear message when a real provider is selected but not configured."""

    name = "not_configured"
    model_name = "external"

    def generate(self, project_id: str, avatar_source_path: str, audio_path: str) -> dict:
        """Raise a configuration error with the expected integration point."""
        raise RuntimeError(
            f"AVATAR_PROVIDER={self.model_name} is selected, but no integration is configured yet. "
            "Use AVATAR_PROVIDER=placeholder or connect a GPU worker/API provider."
        )


class Wav2LipProvider(NotConfiguredAvatarProvider):
    """Future Wav2Lip integration point."""

    name = "wav2lip"
    model_name = "wav2lip"


class SadTalkerProvider(NotConfiguredAvatarProvider):
    """Future SadTalker integration point."""

    name = "sadtalker"
    model_name = "sadtalker"


class MuseTalkProvider(NotConfiguredAvatarProvider):
    """Future MuseTalk integration point."""

    name = "musetalk"
    model_name = "musetalk"


class ApiAvatarProvider(NotConfiguredAvatarProvider):
    """Future remote GPU/API integration point."""

    name = "api"
    model_name = "api"

    def generate(self, project_id: str, avatar_source_path: str, audio_path: str) -> dict:
        """Signal the remote API contract expected for a production GPU worker."""
        endpoint = os.getenv("AVATAR_API_URL", "")
        if not endpoint:
            raise RuntimeError(
                "AVATAR_PROVIDER=api requires AVATAR_API_URL. The API should accept project_id, "
                "avatar_source_path, and audio_path, then return an MP4 path or downloadable URL."
            )
        raise RuntimeError("Remote avatar API client is scaffolded but not implemented yet.")
