from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def normalize_output_format(output_format: str) -> str:
    return output_format.strip().lower()


def output_format_from_path(path: Path | None) -> str | None:
    if path is None or not path.suffix:
        return None
    return normalize_output_format(path.suffix.removeprefix("."))


def output_suffix(output_format: str) -> str:
    normalized = normalize_output_format(output_format)
    if normalized == "aiff":
        return ".aiff"
    return f".{normalized}"


def ensure_output_path(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(value: str) -> str:
    cleaned = []
    for character in value.strip():
        if character.isalnum() or character in {"-", "_"}:
            cleaned.append(character)
        else:
            cleaned.append("_")
    result = "".join(cleaned).strip("._")
    return result or "voice"


def resolve_output_path(
    output_path: Path | None,
    *,
    provider: str,
    voice: str,
    output_format: str,
) -> Path:
    suffix = output_suffix(output_format)
    if output_path is not None:
        if output_path.suffix:
            return output_path
        return output_path.with_suffix(suffix)
    return Path.cwd() / f"{sanitize_filename(provider)}_{sanitize_filename(voice)}{suffix}"


def convert_audio_with_ffmpeg(
    input_path: Path,
    output_path: Path,
    *,
    format: str,
    ffmpeg_path: Path | None = None,
) -> None:
    executable = str(ffmpeg_path) if ffmpeg_path is not None else (shutil.which("ffmpeg") or "ffmpeg")
    command = [
        executable,
        "-y",
        "-i",
        str(input_path),
    ]
    if format == "mp3":
        command.extend(["-codec:a", "libmp3lame"])
    elif format == "flac":
        command.extend(["-codec:a", "flac"])
    elif format in {"wav", "wave"}:
        command.extend(["-codec:a", "pcm_s16le"])
    elif format in {"aiff", "aif"}:
        command.extend(["-codec:a", "pcm_s16be"])
    command.append(str(output_path))
    subprocess.run(command, check=True, capture_output=True, text=True)
