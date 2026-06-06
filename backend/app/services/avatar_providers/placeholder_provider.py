"""Placeholder avatar provider used until real talking-head models are connected."""

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw

from app.services.avatar_providers.base import AvatarProvider
from app.services.avatar_providers.media_helpers import audio_duration, output_paths
from app.services.ffmpeg_service import resolve_binary
from app.services.storage_service import STORAGE_DIR, storage_url


class PlaceholderAvatarProvider(AvatarProvider):
    """Generate a static avatar card video synchronized to narration audio."""

    name = "placeholder"

    def _avatar_card(self, avatar_source_path: str, output_image: Path) -> None:
        """Create a simple avatar preview card from an uploaded image or video marker."""
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

    def generate(self, project_id: str, avatar_source_path: str, audio_path: str) -> dict:
        """Generate a placeholder avatar MP4, or a static preview if FFmpeg is unavailable."""
        preview_image, output_video = output_paths(project_id, audio_path, STORAGE_DIR)
        self._avatar_card(avatar_source_path, preview_image)
        duration = audio_duration(audio_path)
        ffmpeg = resolve_binary("ffmpeg")
        if not ffmpeg:
            return {
                "path": str(preview_image),
                "url": storage_url(preview_image),
                "duration_seconds": duration,
                "provider": self.name,
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
        except Exception as error:
            return {
                "path": str(preview_image),
                "url": storage_url(preview_image),
                "duration_seconds": duration,
                "provider": self.name,
                "status": "image_preview_only",
                "message": f"Placeholder MP4 generation failed: {error}",
            }
        return {
            "path": str(output_video),
            "url": storage_url(output_video),
            "duration_seconds": duration,
            "provider": self.name,
            "status": "video_generated",
        }
