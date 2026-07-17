"""Avatar provider package for swappable talking-avatar backends."""

from app.services.avatar_providers.animated_2d_provider import Animated2DAvatarProvider
from app.services.avatar_providers.external_provider import (
    ApiAvatarProvider,
    MuseTalkProvider,
    SadTalkerProvider,
    Wav2LipProvider,
)
from app.services.avatar_providers.placeholder_provider import PlaceholderAvatarProvider


PROVIDERS = {
    "animated": Animated2DAvatarProvider,
    "animated_2d": Animated2DAvatarProvider,
    "placeholder": PlaceholderAvatarProvider,
    "wav2lip": Wav2LipProvider,
    "sadtalker": SadTalkerProvider,
    "musetalk": MuseTalkProvider,
    "api": ApiAvatarProvider,
}
