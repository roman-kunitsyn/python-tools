from __future__ import annotations

from pathlib import Path


def normalize_output_format(output_format: str) -> str:
    return output_format.strip().lower()


def output_suffix(output_format: str) -> str:
    normalized = normalize_output_format(output_format)
    if normalized == "aiff":
        return ".aiff"
    return f".{normalized}"


def ensure_output_path(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
