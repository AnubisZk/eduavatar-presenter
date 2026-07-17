"""Natural and cloned text-to-speech providers for presentation narration."""

import asyncio
import importlib.util
import os
import subprocess
import threading
import wave
from pathlib import Path
from typing import List

from pydantic import BaseModel

from app.services.avatar_providers.media_helpers import audio_duration
from app.services.ffmpeg_service import resolve_binary
from app.services.storage_service import STORAGE_DIR, storage_url


class ScriptSection(BaseModel):
    """Slide-level narration section consumed by the selected TTS provider."""

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


EDGE_VOICES = {
    "english": "en-US-AriaNeural",
    "turkish": "tr-TR-EmelNeural",
    "german": "de-DE-KatjaNeural",
    "french": "fr-FR-DeniseNeural",
    "spanish": "es-ES-ElviraNeural",
    "italian": "it-IT-ElsaNeural",
    "arabic": "ar-SA-ZariyahNeural",
}

XTTS_LANGUAGE_CODES = {
    "english": "en",
    "turkish": "tr",
    "german": "de",
    "french": "fr",
    "spanish": "es",
    "italian": "it",
    "arabic": "ar",
}

_XTTS_ENGINE = None
_XTTS_ENGINE_DEVICE = ""
_XTTS_LOCK = threading.Lock()


def selected_tts_provider_name() -> str:
    """Return the configured voice provider name."""
    return os.getenv("TTS_PROVIDER", "edge").strip().lower() or "edge"


def voice_provider_capabilities() -> dict:
    """Describe providers that can run in the current backend process."""
    xtts_available = all(importlib.util.find_spec(module) is not None for module in ("torch", "TTS"))
    xtts_reason = ""
    if not xtts_available:
        xtts_reason = (
            "Uploaded-voice cloning is not enabled on this backend. "
            "Install a compatible PyTorch build and backend/requirements-xtts.txt, "
            "or select the standard neural voice."
        )
    return {
        "edge": {"available": True, "label": "Standard neural voice"},
        "xtts": {
            "available": xtts_available,
            "label": "Uploaded voice clone with XTTS",
            "reason": xtts_reason,
        },
        "placeholder": {"available": True, "label": "Silent pipeline test"},
    }


async def _write_edge_speech(path: Path, text: str, voice: str) -> None:
    """Generate one spoken narration file with Edge TTS."""
    try:
        import edge_tts
    except ImportError as error:
        raise RuntimeError("TTS_PROVIDER=edge requires the edge-tts package.") from error

    rate = os.getenv("EDGE_TTS_RATE", "+0%")
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(path))


def _prepare_xtts_reference(audio_dir: Path, voice_sample_path: str) -> Path:
    """Normalize an uploaded reference to a clean, bounded mono WAV file."""
    source = Path(voice_sample_path)
    if not source.is_file():
        raise FileNotFoundError(f"Uploaded voice reference was not found: {source}")

    duration = audio_duration(str(source))
    if duration < 3.0:
        raise ValueError("XTTS voice cloning needs at least 3 seconds of clear speech; 6-30 seconds is recommended.")

    ffmpeg = resolve_binary("ffmpeg")
    if not ffmpeg:
        raise FileNotFoundError("FFmpeg is required to prepare the uploaded XTTS voice reference.")
    reference = audio_dir / "voice_reference_xtts.wav"
    result = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-t",
            "30",
            "-ac",
            "1",
            "-ar",
            "24000",
            "-c:a",
            "pcm_s16le",
            str(reference),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not reference.is_file():
        raise RuntimeError(f"Voice reference conversion failed: {result.stderr.strip()[-1000:]}")
    return reference


def _get_xtts_engine():
    """Load XTTS once per backend process and reuse it for every slide."""
    global _XTTS_ENGINE, _XTTS_ENGINE_DEVICE
    if _XTTS_ENGINE is not None:
        return _XTTS_ENGINE, _XTTS_ENGINE_DEVICE
    try:
        import torch
        from TTS.api import TTS
    except ImportError as error:
        raise RuntimeError(
            "Uploaded-voice cloning is not enabled on this backend. Install a compatible PyTorch build "
            "and backend/requirements-xtts.txt, or select the standard neural voice."
        ) from error

    configured_device = os.getenv("XTTS_DEVICE", "").strip().lower()
    device = configured_device or ("cuda" if torch.cuda.is_available() else "cpu")
    model_name = os.getenv("XTTS_MODEL_NAME", "tts_models/multilingual/multi-dataset/xtts_v2")
    try:
        _XTTS_ENGINE = TTS(model_name).to(device)
    except Exception as error:
        raise RuntimeError(
            "XTTS model loading failed. Check model-license acceptance, model storage, memory, and device settings: "
            f"{error}"
        ) from error
    _XTTS_ENGINE_DEVICE = device
    return _XTTS_ENGINE, _XTTS_ENGINE_DEVICE


def _write_xtts_speech(path: Path, text: str, reference: Path, language_code: str) -> str:
    """Clone the uploaded reference voice and synthesize one slide narration."""
    with _XTTS_LOCK:
        engine, device = _get_xtts_engine()
        engine.tts_to_file(
            text=text,
            speaker_wav=str(reference),
            language=language_code,
            file_path=str(path),
            split_sentences=True,
        )
    return device


def generate_voice(
    project_id: str,
    script_sections: List[ScriptSection],
    target_language: str,
    voice_sample_path: str,
    provider_name: str | None = None,
) -> List[dict]:
    """Generate one narration file per slide with the selected provider.

    Edge TTS supplies a standard neural voice. XTTS uses the uploaded reference
    voice after explicit consent. Set TTS_PROVIDER=placeholder only for offline
    pipeline tests.
    """
    audio_dir = STORAGE_DIR / "audio" / project_id
    audio_dir.mkdir(parents=True, exist_ok=True)
    provider = (provider_name or selected_tts_provider_name()).strip().lower()
    if provider not in {"edge", "xtts", "placeholder"}:
        raise ValueError("Unknown TTS provider. Available providers: edge, xtts, placeholder.")

    configured_voice = os.getenv("EDGE_TTS_VOICE", "").strip()
    voice = configured_voice or EDGE_VOICES.get(target_language.strip().lower(), EDGE_VOICES["english"])
    language_code = XTTS_LANGUAGE_CODES.get(target_language.strip().lower())
    if provider == "xtts" and not language_code:
        raise ValueError(f"XTTS does not have a configured language code for {target_language}.")
    xtts_reference = _prepare_xtts_reference(audio_dir, voice_sample_path) if provider == "xtts" else None
    audio_files = []
    for section in script_sections:
        if provider == "edge":
            output = audio_dir / f"slide_{section.slide_index:03d}.mp3"
            try:
                asyncio.run(_write_edge_speech(output, section.text, voice))
            except Exception as error:
                raise RuntimeError(f"Narration generation failed for slide {section.slide_index}: {error}") from error
            duration = audio_duration(str(output))
            voice_name = voice
            device = "online"
        elif provider == "xtts":
            output = audio_dir / f"slide_{section.slide_index:03d}.wav"
            try:
                device = _write_xtts_speech(output, section.text, xtts_reference, language_code)
            except Exception as error:
                raise RuntimeError(f"Voice cloning failed for slide {section.slide_index}: {error}") from error
            duration = audio_duration(str(output))
            voice_name = "uploaded_voice_clone"
        else:
            output = audio_dir / f"slide_{section.slide_index:03d}.wav"
            _write_silence(output, section.estimated_duration_seconds)
            duration = section.estimated_duration_seconds
            voice_name = "silence"
            device = "offline_test"
        audio_files.append(
            {
                "slide_index": section.slide_index,
                "path": str(output),
                "url": storage_url(output),
                "duration_seconds": duration,
                "language": target_language,
                "provider": provider,
                "voice": voice_name,
                "device": device,
                "voice_sample_path": voice_sample_path,
            }
        )
    return audio_files
