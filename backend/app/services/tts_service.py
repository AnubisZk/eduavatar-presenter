"""Replaceable text-to-speech service interface."""

import wave
from pathlib import Path
from typing import List

from pydantic import BaseModel

from app.services.storage_service import STORAGE_DIR, storage_url


class ScriptSection(BaseModel):
    """Slide-level narration section consumed by the TTS placeholder."""

    slide_index: int
    text: str
    target_language: str
    estimated_duration_seconds: float


def _write_silence(path: Path, duration_seconds: float) -> None:
    """Write a silent WAV file so downstream FFmpeg rendering has valid audio."""
    sample_rate = 16000
    frames = int(sample_rate * max(1.0, duration_seconds))
    with wave.open(str(path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frames)


def generate_voice(
    project_id: str,
    script_sections: List[ScriptSection],
    target_language: str,
    voice_sample_path: str,
) -> List[dict]:
    """Generate placeholder audio files for each section.

    This function is the future integration point for XTTS, OpenVoice, GPT-SoVITS,
    ElevenLabs, or another consent-aware voice generation provider.
    """
    audio_dir = STORAGE_DIR / "audio" / project_id
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []
    for section in script_sections:
        output = audio_dir / f"slide_{section.slide_index:03d}.wav"
        _write_silence(output, section.estimated_duration_seconds)
        audio_files.append(
            {
                "slide_index": section.slide_index,
                "path": str(output),
                "url": storage_url(output),
                "duration_seconds": section.estimated_duration_seconds,
                "language": target_language,
                "voice_sample_path": voice_sample_path,
            }
        )
    return audio_files
