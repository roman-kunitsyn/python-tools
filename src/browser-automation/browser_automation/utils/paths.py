from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def ensure_parent(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def session_timestamp(now: datetime | None = None) -> str:
    current = now or datetime.now()
    return current.strftime("%Y_%m_%d-%H_%M_%S")


def default_session_dir(base_dir: Path | None = None, *, now: datetime | None = None) -> Path:
    return base_dir or Path("logs") / "browser-automation" / session_timestamp(now)


def slugify_url_path(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    if not path:
        return "index"

    slug = re.sub(r"[^A-Za-z0-9._/-]+", "-", path)
    slug = slug.replace("//", "/")
    return slug.strip("/") or "index"


def page_path_for_url(url: str, output_dir: Path, suffix: str) -> Path:
    parsed = urlparse(url)
    slug = slugify_url_path(url)
    if parsed.path.endswith("/") or not parsed.path:
        slug = f"{slug}/index" if slug != "index" else slug
    return output_dir / f"{slug}{suffix}"
