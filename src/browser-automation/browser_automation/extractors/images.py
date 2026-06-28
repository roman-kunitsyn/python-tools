from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin

from browser_automation.utils.html import parse_html


@dataclass(slots=True)
class ExtractedImage:
    url: str
    alt: str | None
    width: int | None
    height: int | None


_IMAGE_ATTRS = (
    "src",
    "data-src",
    "data-lazy-src",
    "data-original",
    "data-bg",
    "data-background",
)


def _parse_srcset(value: str) -> list[str]:
    urls: list[str] = []
    for part in value.split(","):
        candidate = part.strip().split(" ", 1)[0].strip()
        if candidate:
            urls.append(candidate)
    return urls


def _extract_style_urls(value: str) -> list[str]:
    return [match for match in re.findall(r"url\(['\"]?([^'\")]+)['\"]?\)", value)]


def _collect_image_urls(tag: object, base_url: str) -> list[str]:
    try:
        attrs = tag.attrs  # type: ignore[attr-defined]
    except AttributeError:
        return []

    urls: list[str] = []
    for attr in _IMAGE_ATTRS:
        value = attrs.get(attr)
        if isinstance(value, str) and value:
            urls.append(urljoin(base_url, value))

    for attr in ("srcset", "data-srcset"):
        value = attrs.get(attr)
        if isinstance(value, str) and value:
            urls.extend(urljoin(base_url, candidate) for candidate in _parse_srcset(value))

    style_value = attrs.get("style")
    if isinstance(style_value, str) and style_value:
        urls.extend(urljoin(base_url, candidate) for candidate in _extract_style_urls(style_value))

    return urls


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
    seen: set[str] = set()

    for image in soup.find_all(["img", "source", "div", "span", "section", "picture"]):
        candidate_urls = _collect_image_urls(image, base_url)
        if not candidate_urls and image.name == "img" and image.get("src"):
            candidate_urls = [urljoin(base_url, image["src"])]

        width = image.get("width")
        height = image.get("height")

        for candidate_url in candidate_urls:
            if candidate_url in seen:
                continue
            seen.add(candidate_url)
            images.append(
                ExtractedImage(
                    url=candidate_url,
                    alt=image.get("alt"),
                    width=int(width) if width and str(width).isdigit() else None,
                    height=int(height) if height and str(height).isdigit() else None,
                )
            )

    return images
