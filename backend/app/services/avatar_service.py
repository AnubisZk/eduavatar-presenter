"""Replaceable placeholder avatar video service."""

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from app.services.ffmpeg_service import resolve_binary
from app.services.storage_service import STORAGE_DIR, storage_url


def _audio_duration(audio_path: str) -> float:
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


def _avatar_card(project_id: str, avatar_source_path: str, output_image: Path) -> None:
    """Create a simple avatar preview card from an uploaded image or a generic video marker."""
    canvas = Image.new("RGB", (640, 640), "#e0f2fe")
    draw = ImageDraw.Draw(canvas)
    source = Path(avatar_source_path)
    if source.suffix.lower() in {".jpg", ".jpeg", ".png"} and source.exists():
        face = Image.open(source).convert("RGB")
        face.thumbnail((520, 520))
        x = (640 - face.width) // 2
        y = (640 - face.height) // 2
        canvas.paste(face, (x, y))
    else:
        draw.ellipse((170, 110, 470, 410), fill="#bfdbfe", outline="#1d4ed8", width=6)
        draw.rectangle((150, 410, 490, 590), fill="#1d4ed8")
        draw.text((190, 300), "Avatar source video", fill="#0f172a")
    draw.rectangle((0, 560, 640, 640), fill="#0f172a")
    draw.text((28, 588), "Placeholder talking avatar clip", fill="white")
    canvas.save(output_image)


def generate_avatar_video(project_id: str, avatar_source_path: str, audio_path: str) -> dict:
    """Generate a placeholder avatar clip synchronized to one audio file.

    This is the future integration point for MuseTalk, SadTalker, or Wav2Lip.
    """
    avatar_dir = STORAGE_DIR / "avatars" / project_id
    avatar_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(audio_path).stem
    preview_image = avatar_dir / f"{stem}_avatar.png"
    output_video = avatar_dir / f"{stem}_avatar.mp4"
    _avatar_card(project_id, avatar_source_path, preview_image)
    duration = _audio_duration(audio_path)
    ffmpeg = resolve_binary("ffmpeg")
    if not ffmpeg:
        return {
            "path": str(preview_image),
            "url": storage_url(preview_image),
            "duration_seconds": duration,
            "status": "image_preview_only",
            "message": "FFmpeg is required to create MP4 avatar clips.",
        }
    try:
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loop",
                "1",
                "-i",
                str(preview_image),
                "-i",
                audio_path,
                "-t",
                str(duration),
                "-vf",
                "scale=480:480,format=yuv420p",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-shortest",
                str(output_video),
            ],
            check=True,
            capture_output=True,
        )
    except Exception:
        # If FFmpeg is missing, keep the image preview and report it for development visibility.
        return {"path": str(preview_image), "url": storage_url(preview_image), "duration_seconds": duration}
    return {"path": str(output_video), "url": storage_url(output_video), "duration_seconds": duration}
