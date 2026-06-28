from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


_BLOCK_TAGS = {"p", "div", "section", "article", "header", "footer", "nav", "aside", "li", "tr", "table", "thead", "tbody", "tfoot", "br"}


def strip_embedded_content(html: str, *, strip_navigation: bool = False) -> str:
    patterns = [r"<script\b[^>]*>.*?</script>", r"<style\b[^>]*>.*?</style>"]
    if strip_navigation:
        patterns.extend(
            [
                r"<nav\b[^>]*>.*?</nav>",
                r"<header\b[^>]*>.*?</header>",
                r"<footer\b[^>]*>.*?</footer>",
                r"<aside\b[^>]*>.*?</aside>",
            ]
        )

    cleaned = html
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)
    return cleaned


@dataclass(slots=True)
class SimpleHtmlData:
    text_parts: list[str] = field(default_factory=list)
    links: list[tuple[str, str]] = field(default_factory=list)
    images: list[dict[str, str | None]] = field(default_factory=list)
    headings: list[tuple[int, str]] = field(default_factory=list)


class SimpleHtmlParser(HTMLParser):
    def __init__(self, base_url: str | None = None) -> None:
        super().__init__()
        self.base_url = base_url
        self.data = SimpleHtmlData()
        self._tag_stack: list[str] = []
        self._current_heading: int | None = None
        self._heading_buffer: list[str] = []
        self._anchor_href: str | None = None
        self._anchor_buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._tag_stack.append(tag)
        attr_map = dict(attrs)
        if tag == "a":
            self._anchor_href = attr_map.get("href")
            self._anchor_buffer = []
        elif tag == "img":
            src = attr_map.get("src")
            if src:
                resolved = urljoin(self.base_url or "", src)
                self.data.images.append(
                    {
                        "url": resolved,
                        "alt": attr_map.get("alt"),
                        "width": attr_map.get("width"),
                        "height": attr_map.get("height"),
                    }
                )
        elif tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
            self._current_heading = int(tag[1])
            self._heading_buffer = []
        elif tag in _BLOCK_TAGS:
            self.data.text_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._tag_stack:
            self._tag_stack.pop()
        if tag == "a" and self._anchor_href is not None:
            link_text = "".join(self._anchor_buffer).strip()
            self.data.links.append((self._anchor_href, link_text))
            self._anchor_href = None
            self._anchor_buffer = []
        elif self._current_heading is not None and tag == f"h{self._current_heading}":
            heading_text = "".join(self._heading_buffer).strip()
            self.data.headings.append((self._current_heading, heading_text))
            self._current_heading = None
            self._heading_buffer = []
            self.data.text_parts.append("\n")
        elif tag in _BLOCK_TAGS:
            self.data.text_parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        if self._anchor_href is not None:
            self._anchor_buffer.append(data)
        if self._current_heading is not None:
            self._heading_buffer.append(data)
        self.data.text_parts.append(data)

    def get_text(self) -> str:
        text = "".join(self.data.text_parts)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def parse_html(html: str, base_url: str | None = None) -> SimpleHtmlParser:
    parser = SimpleHtmlParser(base_url)
    parser.feed(html)
    return parser
