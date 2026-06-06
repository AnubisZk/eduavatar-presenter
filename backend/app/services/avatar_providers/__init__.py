"""Avatar provider package for swappable talking-avatar backends."""

from app.services.avatar_providers.external_provider import (
    ApiAvatarProvider,
    MuseTalkProvider,
    SadTalkerProvider,
    Wav2LipProvider,
)
from app.services.avatar_providers.placeholder_provider import PlaceholderAvatarProvider


PROVIDERS = {
    "placeholder": PlaceholderAvatarProvider,
    "wav2lip": Wav2LipProvider,
    "sadtalker": SadTalkerProvider,
    "musetalk": MuseTalkProvider,
    "api": ApiAvatarProvider,
}
