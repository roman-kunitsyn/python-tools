from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from browser_automation.utils.html import parse_html


@dataclass(slots=True)
class ExtractedLink:
    url: str
    text: str
    is_internal: bool


def extract_links(html: str, base_url: str) -> list[ExtractedLink]:
    try:
        from bs4 import BeautifulSoup
    except ImportError:  # pragma: no cover - runtime dependency fallback
        parser = parse_html(html, base_url)
        parsed_base = urlparse(base_url)
        links: list[ExtractedLink] = []
        for href, text in parser.data.links:
            url = urljoin(base_url, href)
            parsed = urlparse(url)
            links.append(
                ExtractedLink(
                    url=url,
                    text=text,
                    is_internal=parsed.scheme in {"http", "https"} and parsed.netloc == parsed_base.netloc,
                )
            )
        return links

    base = urlparse(base_url)
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:  # pragma: no cover - parser backend fallback
        soup = BeautifulSoup(html, "html.parser")
    links: list[ExtractedLink] = []

    for anchor in soup.find_all("a", href=True):
        url = urljoin(base_url, anchor["href"])
        parsed = urlparse(url)
        text = anchor.get_text(" ", strip=True)
        is_internal = parsed.scheme in {"http", "https"} and parsed.netloc == base.netloc
        links.append(ExtractedLink(url=url, text=text, is_internal=is_internal))

    return links
