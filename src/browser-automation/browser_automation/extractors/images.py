from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from browser_automation.utils.html import parse_html


@dataclass(slots=True)
class ExtractedImage:
    url: str
    alt: str | None
    width: int | None
    height: int | None


def extract_images(html: str, base_url: str) -> list[ExtractedImage]:
    try:
        from bs4 import BeautifulSoup
    except ImportError:  # pragma: no cover - runtime dependency fallback
        parser = parse_html(html, base_url)
        images: list[ExtractedImage] = []
        for image in parser.data.images:
            width = image.get("width")
            height = image.get("height")
            images.append(
                ExtractedImage(
                    url=str(image["url"]),
                    alt=image.get("alt"),
                    width=int(width) if width and str(width).isdigit() else None,
                    height=int(height) if height and str(height).isdigit() else None,
                )
            )
        return images

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:  # pragma: no cover - parser backend fallback
        soup = BeautifulSoup(html, "html.parser")
    images: list[ExtractedImage] = []

    for image in soup.find_all("img", src=True):
        width = image.get("width")
        height = image.get("height")
        images.append(
            ExtractedImage(
                url=urljoin(base_url, image["src"]),
                alt=image.get("alt"),
                width=int(width) if width and str(width).isdigit() else None,
                height=int(height) if height and str(height).isdigit() else None,
            )
        )

    return images
