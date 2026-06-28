from __future__ import annotations

from browser_automation.extractors.html import clean_html
from browser_automation.utils.html import parse_html


def html_to_markdown(html: str, *, strip_navigation: bool = False) -> str:
    cleaned_html = clean_html(html, strip_navigation=strip_navigation)

    try:
        from markdownify import markdownify as markdownify_html
    except ImportError:  # pragma: no cover - runtime dependency fallback
        parser = parse_html(cleaned_html)
        lines: list[str] = []
        for level, heading in parser.data.headings:
            lines.append(f"{'#' * level} {heading}".strip())
        text = parser.get_text()
        if text:
            lines.append(text)
        return "\n\n".join(line for line in lines if line).strip()

    return markdownify_html(cleaned_html, heading_style="ATX")
