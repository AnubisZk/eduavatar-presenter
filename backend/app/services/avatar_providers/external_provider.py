"""CLI and remote integrations for GPU talking-avatar models."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from app.services.avatar_providers.base import AvatarProvider
from app.services.avatar_providers.media_helpers import audio_duration, output_paths
from app.services.storage_service import STORAGE_DIR, storage_url


class NotConfiguredAvatarProvider(AvatarProvider):
    """Return a clear message when a real provider is selected but not configured."""

    name = "not_configured"
    model_name = "external"

    def generate(self, project_id: str, avatar_source_path: str, audio_path: str) -> dict:
        """Raise a configuration error with the expected integration point."""
        raise RuntimeError(
            f"AVATAR_PROVIDER={self.model_name} is selected, but no integration is configured yet. "
            "Use AVATAR_PROVIDER=animated or configure the selected GPU worker/API provider."
        )


class Wav2LipProvider(AvatarProvider):
    """Run a local Wav2Lip checkout through its supported inference CLI."""

    name = "wav2lip"

    def generate(self, project_id: str, avatar_source_path: str, audio_path: str) -> dict:
        home = Path(os.getenv("WAV2LIP_HOME", "")).expanduser()
        checkpoint = Path(os.getenv("WAV2LIP_CHECKPOINT", "")).expanduser()
        inference = home / "inference.py"
        if not inference.is_file() or not checkpoint.is_file():
            raise RuntimeError(
                "AVATAR_PROVIDER=wav2lip requires WAV2LIP_HOME and WAV2LIP_CHECKPOINT."
            )
        _, output_video = output_paths(project_id, audio_path, STORAGE_DIR)
        python = os.getenv("WAV2LIP_PYTHON", sys.executable)
        result = subprocess.run(
            [
                python,
                str(inference),
                "--checkpoint_path",
                str(checkpoint),
                "--face",
                avatar_source_path,
                "--audio",
                audio_path,
                "--outfile",
                str(output_video),
            ],
            cwd=str(home),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 or not output_video.is_file():
            details = (result.stderr or result.stdout).strip()[-2000:]
            raise RuntimeError(f"Wav2Lip inference failed: {details}")
        return {
            "path": str(output_video),
            "url": storage_url(output_video),
            "duration_seconds": audio_duration(audio_path),
            "provider": self.name,
            "status": "video_generated",
        }


class SadTalkerProvider(AvatarProvider):
    """Run a local SadTalker checkout through its supported inference CLI."""

    name = "sadtalker"

    def generate(self, project_id: str, avatar_source_path: str, audio_path: str) -> dict:
        home = Path(os.getenv("SADTALKER_HOME", "")).expanduser()
        inference = home / "inference.py"
        if not inference.is_file():
            raise RuntimeError("AVATAR_PROVIDER=sadtalker requires SADTALKER_HOME.")

        _, output_video = output_paths(project_id, audio_path, STORAGE_DIR)
        python = os.getenv("SADTALKER_PYTHON", sys.executable)
        preprocess = os.getenv("SADTALKER_PREPROCESS", "crop")
        expression_scale = os.getenv("SADTALKER_EXPRESSION_SCALE", "1.0")
        with tempfile.TemporaryDirectory(prefix="sadtalker_", dir=str(output_video.parent)) as result_dir:
            command = [
                python,
                str(inference),
                "--driven_audio",
                audio_path,
                "--source_image",
                avatar_source_path,
                "--result_dir",
                result_dir,
                "--preprocess",
                preprocess,
                "--expression_scale",
                expression_scale,
            ]
            if os.getenv("SADTALKER_STILL", "true").lower() in {"1", "true", "yes"}:
                command.append("--still")
            enhancer = os.getenv("SADTALKER_ENHANCER", "").strip()
            if enhancer:
                command.extend(["--enhancer", enhancer])

            result = subprocess.run(command, cwd=str(home), capture_output=True, text=True)
            candidates = sorted(Path(result_dir).rglob("*.mp4"), key=lambda path: path.stat().st_mtime)
            if result.returncode != 0 or not candidates:
                details = (result.stderr or result.stdout).strip()[-2000:]
                raise RuntimeError(f"SadTalker inference failed: {details}")
            shutil.copy2(candidates[-1], output_video)

        return {
            "path": str(output_video),
            "url": storage_url(output_video),
            "duration_seconds": audio_duration(audio_path),
            "provider": self.name,
            "status": "video_generated",
        }


class MuseTalkProvider(NotConfiguredAvatarProvider):
    """Future MuseTalk integration point."""

    name = "musetalk"
    model_name = "musetalk"


class ApiAvatarProvider(NotConfiguredAvatarProvider):
    """Future remote GPU/API integration point."""

    name = "api"
    model_name = "api"

    def generate(self, project_id: str, avatar_source_path: str, audio_path: str) -> dict:
        """Signal the remote API contract expected for a production GPU worker."""
        endpoint = os.getenv("AVATAR_API_URL", "")
        if not endpoint:
            raise RuntimeError(
                "AVATAR_PROVIDER=api requires AVATAR_API_URL. The API should accept project_id, "
                "avatar_source_path, and audio_path, then return an MP4 path or downloadable URL."
            )
        raise RuntimeError("Remote avatar API client is scaffolded but not implemented yet.")
