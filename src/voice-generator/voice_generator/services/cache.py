from __future__ import annotations

from pathlib import Path


def resolve_cache_path(cache_directory: Path | None, name: str) -> Path | None:
    if cache_directory is None:
        return None
    return cache_directory / name
