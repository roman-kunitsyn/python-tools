from __future__ import annotations

from browser_automation.utils.html import strip_embedded_content


def clean_html(html: str, *, strip_navigation: bool = False) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError:  # pragma: no cover - runtime dependency fallback
        return strip_embedded_content(html, strip_navigation=strip_navigation)

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:  # pragma: no cover - parser backend fallback
        soup = BeautifulSoup(html, "html.parser")

    for tag_name in ("script", "style"):
        for tag in soup.find_all(tag_name):
            tag.decompose()

    if strip_navigation:
        for tag_name in ("nav", "header", "footer", "aside"):
            for tag in soup.find_all(tag_name):
                tag.decompose()

    return str(soup)
