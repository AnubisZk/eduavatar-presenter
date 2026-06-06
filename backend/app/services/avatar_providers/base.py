"""Shared avatar provider interface."""

from abc import ABC, abstractmethod


class AvatarProvider(ABC):
    """Base class for avatar generation providers."""

    name = "base"

    @abstractmethod
    def generate(self, project_id: str, avatar_source_path: str, audio_path: str) -> dict:
        """Generate one avatar clip for one audio file."""
