"""CPU-friendly talking portrait animation synchronized to narration amplitude."""

import math
import subprocess
from array import array
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps

from app.services.avatar_providers.base import AvatarProvider
from app.services.avatar_providers.media_helpers import audio_duration, output_paths
from app.services.ffmpeg_service import resolve_binary
from app.services.storage_service import STORAGE_DIR, storage_url


class Animated2DAvatarProvider(AvatarProvider):
    """Animate a portrait locally without a GPU or external avatar API.

    The mouth opening follows the narration waveform while the portrait receives a
    restrained breathing/head motion. Face detection is used when OpenCV is
    installed; otherwise a centered portrait composition is assumed.
    """

    name = "animated_2d"
    size = 640
    fps = 25
    envelope_rate = 100

    def _load_portrait(self, source_path: str, preview_path: Path, ffmpeg: str) -> Image.Image:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Avatar source was not found: {source}")

        if source.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            portrait = Image.open(source).convert("RGB")
        elif source.suffix.lower() in {".mp4", ".mov", ".m4v", ".webm"}:
            subprocess.run(
                [ffmpeg, "-y", "-loglevel", "error", "-i", str(source), "-frames:v", "1", str(preview_path)],
                check=True,
                capture_output=True,
            )
            portrait = Image.open(preview_path).convert("RGB")
        else:
            raise ValueError("Animated avatar input must be a portrait image or short video.")

        canvas = ImageOps.fit(
            portrait,
            (self.size, self.size),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.38),
        )
        canvas.save(preview_path)
        return canvas

    def _detect_face(self, portrait: Image.Image) -> tuple[int, int, int, int]:
        """Return the largest detected face, with a portrait-friendly fallback."""
        try:
            import cv2
            import numpy as np

            gray = cv2.cvtColor(np.asarray(portrait), cv2.COLOR_RGB2GRAY)
            cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(120, 120))
            if len(faces):
                x, y, width, height = max(faces, key=lambda item: int(item[2]) * int(item[3]))
                return int(x), int(y), int(width), int(height)
        except (ImportError, AttributeError, RuntimeError, ValueError):
            pass
        return 112, 48, 416, 520

    def _audio_envelope(self, audio_path: str, ffmpeg: str) -> list[float]:
        """Decode audio to a small normalized amplitude envelope."""
        decoded = subprocess.run(
            [
                ffmpeg,
                "-v",
                "error",
                "-i",
                audio_path,
                "-ac",
                "1",
                "-ar",
                str(self.envelope_rate),
                "-f",
                "s16le",
                "pipe:1",
            ],
            check=True,
            capture_output=True,
        )
        samples = array("h")
        samples.frombytes(decoded.stdout)
        values = [abs(int(sample)) for sample in samples]
        if not values:
            return [0.0]

        smoothed = []
        for index in range(len(values)):
            window = values[max(0, index - 2) : min(len(values), index + 3)]
            smoothed.append(sum(window) / len(window))

        ordered = sorted(smoothed)
        noise_floor = ordered[int((len(ordered) - 1) * 0.12)]
        speech_peak = ordered[int((len(ordered) - 1) * 0.95)]
        span = max(1.0, speech_peak - noise_floor)
        return [max(0.0, min(1.0, (value - noise_floor) / span)) for value in smoothed]

    def _move_mouth(
        self,
        portrait: Image.Image,
        face: tuple[int, int, int, int],
        amount: float,
    ) -> Image.Image:
        """Create a feathered jaw/lip opening in the estimated mouth region."""
        if amount < 0.025:
            return portrait.copy()

        x, y, width, height = face
        left = max(0, int(x + width * 0.25))
        right = min(self.size, int(x + width * 0.75))
        top = max(0, int(y + height * 0.58))
        bottom = min(self.size, int(y + height * 0.84))
        region = portrait.crop((left, top, right, bottom))
        region_width, region_height = region.size
        split = int(region_height * 0.52)
        shift = max(1, int((amount**0.72) * min(14, region_height * 0.16)))

        animated = region.copy()
        draw = ImageDraw.Draw(animated)
        mouth_width = int(region_width * 0.56)
        gap_left = (region_width - mouth_width) // 2
        draw.ellipse(
            (gap_left, split - shift, gap_left + mouth_width, split + shift),
            fill=(38, 14, 20),
        )
        upper = region.crop((0, 0, region_width, split))
        lower = region.crop((0, split, region_width, region_height))
        animated.paste(upper, (0, -shift))
        animated.paste(lower, (0, split + shift))

        mask = Image.new("L", region.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse(
            (int(region_width * 0.08), 2, int(region_width * 0.92), region_height - 2),
            fill=225,
        )
        mask = mask.filter(ImageFilter.GaussianBlur(radius=max(3, region_height // 18)))
        frame = portrait.copy()
        frame.paste(animated, (left, top), mask)
        return frame

    def _add_head_motion(self, frame: Image.Image, time_seconds: float, amount: float) -> Image.Image:
        """Apply restrained zoom and vertical movement so the portrait feels alive."""
        zoom = 1.012 + 0.006 * math.sin(time_seconds * math.pi * 0.7) + 0.006 * amount
        scaled_size = max(self.size + 2, int(self.size * zoom))
        scaled = frame.resize((scaled_size, scaled_size), Image.Resampling.LANCZOS)
        margin = (scaled_size - self.size) // 2
        bob = int(2.0 * math.sin(time_seconds * math.pi * 1.1))
        top = max(0, min(scaled_size - self.size, margin + bob))
        return scaled.crop((margin, top, margin + self.size, top + self.size))

    def generate(self, project_id: str, avatar_source_path: str, audio_path: str) -> dict:
        """Render a lip-synced MP4 from a portrait and one narration file."""
        preview_image, output_video = output_paths(project_id, audio_path, STORAGE_DIR)
        ffmpeg = resolve_binary("ffmpeg")
        if not ffmpeg:
            raise FileNotFoundError("FFmpeg is required for animated avatar generation.")

        portrait = self._load_portrait(avatar_source_path, preview_image, ffmpeg)
        face = self._detect_face(portrait)
        envelope = self._audio_envelope(audio_path, ffmpeg)
        duration = audio_duration(audio_path)
        frame_count = max(1, math.ceil(duration * self.fps))

        command = [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{self.size}x{self.size}",
            "-r",
            str(self.fps),
            "-i",
            "pipe:0",
            "-i",
            audio_path,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "21",
            "-c:a",
            "aac",
            "-pix_fmt",
            "yuv420p",
            "-shortest",
            str(output_video),
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            if process.stdin is None:
                raise RuntimeError("FFmpeg input pipe could not be created.")
            for frame_index in range(frame_count):
                time_seconds = frame_index / self.fps
                envelope_index = min(len(envelope) - 1, int(time_seconds * self.envelope_rate))
                amount = envelope[envelope_index]
                frame = self._move_mouth(portrait, face, amount)
                frame = self._add_head_motion(frame, time_seconds, amount)
                process.stdin.write(frame.convert("RGB").tobytes())
            process.stdin.close()
            error_output = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            return_code = process.wait()
            if return_code != 0:
                raise RuntimeError(error_output.strip() or f"FFmpeg exited with code {return_code}.")
        except Exception:
            if process.poll() is None:
                process.kill()
            raise

        return {
            "path": str(output_video),
            "url": storage_url(output_video),
            "duration_seconds": duration,
            "provider": self.name,
            "status": "video_generated",
            "face_detection": "opencv_or_portrait_fallback",
        }
