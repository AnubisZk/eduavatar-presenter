"""Avatar generation service with provider selection."""

import os

from app.services.avatar_providers import PROVIDERS


def selected_avatar_provider_name() -> str:
    """Return the configured avatar provider name."""
    return os.getenv("AVATAR_PROVIDER", "animated").strip().lower() or "animated"


def get_avatar_provider(provider_name: str | None = None):
    """Instantiate the requested provider, falling back to server configuration."""
    provider_name = (provider_name or selected_avatar_provider_name()).strip().lower()
    provider_class = PROVIDERS.get(provider_name)
    if not provider_class:
        available = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Unknown AVATAR_PROVIDER '{provider_name}'. Available providers: {available}.")
    return provider_class()


def generate_avatar_video(
    project_id: str,
    avatar_source_path: str,
    audio_path: str,
    provider_name: str | None = None,
) -> dict:
    """Generate one avatar clip using the configured provider.

    Set AVATAR_PROVIDER to animated, placeholder, wav2lip, sadtalker, musetalk,
    or api. The animated provider works locally on CPU; Wav2Lip and SadTalker use
    separately installed model checkouts.
    """
    provider = get_avatar_provider(provider_name)
    return provider.generate(project_id, avatar_source_path, audio_path)
