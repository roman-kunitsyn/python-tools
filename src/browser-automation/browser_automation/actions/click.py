from __future__ import annotations


def click(page: object, selector: str, *, timeout: int | None = None) -> None:
    kwargs = {}
    if timeout is not None:
        kwargs["timeout"] = timeout
    page.click(selector, **kwargs)  # type: ignore[attr-defined]
