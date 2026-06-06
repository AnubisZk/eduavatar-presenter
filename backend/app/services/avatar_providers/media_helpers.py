"""Media helpers shared by avatar providers."""

import subprocess
from pathlib import Path

from app.services.ffmpeg_service import resolve_binary


def audio_duration(audio_path: str) -> float:
    """Return audio duration using ffprobe, or a safe default if unavailable."""
    ffprobe = resolve_binary("ffprobe")
    if not ffprobe:
        return 5.0
    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return max(1.0, float(result.stdout.strip()))
    except Exception:
        return 5.0


def output_paths(project_id: str, audio_path: str, storage_dir: Path) -> tuple[Path, Path]:
    """Return preview image and MP4 paths for an avatar provider output."""
    avatar_dir = storage_dir / "avatars" / project_id
    avatar_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(audio_path).stem
    return avatar_dir / f"{stem}_avatar.png", avatar_dir / f"{stem}_avatar.mp4"
