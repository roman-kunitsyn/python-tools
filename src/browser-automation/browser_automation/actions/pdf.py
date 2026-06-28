from __future__ import annotations

from pathlib import Path


def pdf(page: object, output_path: Path, *, print_background: bool = True) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    page.pdf(path=str(output_path), print_background=print_background)  # type: ignore[attr-defined]
    return output_path
