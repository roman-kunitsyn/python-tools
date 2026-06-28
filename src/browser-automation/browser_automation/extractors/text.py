from __future__ import annotations

from browser_automation.extractors.html import clean_html
from browser_automation.utils.html import parse_html


def extract_text(html: str, *, strip_navigation: bool = False) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError:  # pragma: no cover - runtime dependency fallback
        return parse_html(clean_html(html, strip_navigation=strip_navigation)).get_text()

    cleaned_html = clean_html(html, strip_navigation=strip_navigation)
    try:
        soup = BeautifulSoup(cleaned_html, "lxml")
    except Exception:  # pragma: no cover - parser backend fallback
        soup = BeautifulSoup(cleaned_html, "html.parser")
    return soup.get_text(separator="\n", strip=True)
