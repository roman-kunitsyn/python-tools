from __future__ import annotations

from pathlib import Path


def screenshot(
    page: object,
    output_path: Path,
    *,
    full_page: bool = False,
    selector: str | None = None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if selector is not None:
        page.locator(selector).screenshot(path=str(output_path))  # type: ignore[attr-defined]
    else:
        page.screenshot(path=str(output_path), full_page=full_page)  # type: ignore[attr-defined]
    return output_path
