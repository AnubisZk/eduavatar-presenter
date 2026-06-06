"""FFmpeg-based final video composition service."""

import subprocess
from pathlib import Path
from typing import List

from app.services.ffmpeg_service import resolve_binary
from app.services.storage_service import STORAGE_DIR, storage_url


def _duration(audio_path: str) -> float:
    """Read media duration with ffprobe and fall back to five seconds."""
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


def _subtitle_file(path: Path, text: str, duration: float) -> Path:
    """Create a tiny SRT file for one slide segment."""
    srt_path = path.with_suffix(".srt")
    safe_text = text.replace("\n", " ").strip()[:500]
    total_seconds = int(duration)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    srt_path.write_text(
        f"1\n00:00:00,000 --> {hours:02d}:{minutes:02d}:{seconds:02d},000\n{safe_text}\n",
        encoding="utf-8",
    )
    return srt_path


def render_final_video(
    project_id: str,
    slide_paths: List[str],
    audio_files: List[str],
    avatar_videos: List[str],
    narration_sections: List[str],
    include_subtitles: bool = True,
) -> dict:
    """Render one MP4 where slides fill the frame and avatar clips sit bottom-right."""
    ffmpeg = resolve_binary("ffmpeg")
    if not ffmpeg:
        raise FileNotFoundError("FFmpeg executable not found on PATH.")
    output_dir = STORAGE_DIR / "outputs" / project_id
    output_dir.mkdir(parents=True, exist_ok=True)
    segment_paths = []
    count = min(len(slide_paths), len(audio_files), len(avatar_videos))
    for index in range(count):
        slide = slide_paths[index]
        audio = audio_files[index]
        avatar = avatar_videos[index]
        duration = _duration(audio)
        segment = output_dir / f"segment_{index + 1:03d}.mp4"
        subtitle = _subtitle_file(segment, narration_sections[index] if index < len(narration_sections) else "", duration)
        filter_chain = (
            "[0:v]scale=1280:720,setsar=1[slide];"
            "[1:v]scale=260:260,setsar=1[avatar];"
            "[slide][avatar]overlay=W-w-36:H-h-36[composed]"
        )
        video_map = "[composed]"
        if include_subtitles:
            escaped_srt = str(subtitle).replace("'", "\\'")
            filter_chain += f";[composed]subtitles='{escaped_srt}':force_style='Fontsize=18,Outline=1'[outv]"
            video_map = "[outv]"
        command = [ffmpeg, "-y", "-loop", "1", "-i", slide]
        if Path(avatar).suffix.lower() in {".jpg", ".jpeg", ".png"}:
            command.extend(["-loop", "1"])
        command.extend(
            [
                "-i",
                avatar,
                "-i",
                audio,
                "-t",
                str(duration),
                "-filter_complex",
                filter_chain,
                "-map",
                video_map,
                "-map",
                "2:a",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-pix_fmt",
                "yuv420p",
                "-shortest",
                str(segment),
            ]
        )
        subprocess.run(
            command,
            check=True,
            capture_output=True,
        )
        segment_paths.append(segment)

    concat_file = output_dir / "segments.txt"
    concat_file.write_text("".join(f"file '{path}'\n" for path in segment_paths), encoding="utf-8")
    final_path = output_dir / "final_presentation.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(final_path),
        ],
        check=True,
        capture_output=True,
    )
    return {"path": str(final_path), "url": storage_url(final_path)}
