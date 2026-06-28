from __future__ import annotations


def fill(page: object, selector: str, value: str, *, timeout: int | None = None) -> None:
    kwargs = {}
    if timeout is not None:
        kwargs["timeout"] = timeout
    page.fill(selector, value, **kwargs)  # type: ignore[attr-defined]
