"""Helpers for locating FFmpeg binaries across common macOS and Linux installs."""

import os
import shutil
from pathlib import Path


def resolve_binary(name: str) -> str | None:
    """Return an executable path for ffmpeg or ffprobe if it is available."""
    env_name = f"{name.upper()}_BINARY"
    if os.environ.get(env_name):
        configured = Path(os.environ[env_name])
        if configured.exists() and configured.is_file():
            return str(configured)

    discovered = shutil.which(name)
    if discovered:
        return discovered

    # Homebrew uses different prefixes on Apple Silicon and Intel Macs.
    for candidate in [
        Path("/opt/homebrew/bin") / name,
        Path("/usr/local/bin") / name,
        Path("/Applications/anaconda3/bin") / name,
        Path.home() / "anaconda3" / "bin" / name,
        Path.home() / "miniconda3" / "bin" / name,
        Path("/usr/bin") / name,
    ]:
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    return None
