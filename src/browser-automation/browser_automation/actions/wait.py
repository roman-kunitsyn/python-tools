from __future__ import annotations


def wait_for(page: object, selector: str, *, timeout: int | None = None) -> None:
    kwargs = {}
    if timeout is not None:
        kwargs["timeout"] = timeout
    page.wait_for_selector(selector, **kwargs)  # type: ignore[attr-defined]
