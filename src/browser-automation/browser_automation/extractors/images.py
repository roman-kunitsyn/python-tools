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
    "data-browser-automation-image-src",
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


def _normalize_live_image_entry(entry: object, base_url: str) -> ExtractedImage | None:
    if not isinstance(entry, dict):
        return None

    url = entry.get("url")
    if not isinstance(url, str) or not url:
        return None

    resolved_url = urljoin(base_url, url)
    alt = entry.get("alt")
    width = entry.get("width")
    height = entry.get("height")

    return ExtractedImage(
        url=resolved_url,
        alt=alt if isinstance(alt, str) else None,
        width=int(width) if isinstance(width, int) else None,
        height=int(height) if isinstance(height, int) else None,
    )


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


def extract_images_from_page(page: object, base_url: str) -> list[ExtractedImage]:
    live_entries: list[dict[str, object]] = []

    try:
        result = page.evaluate(
            """
            () => {
              const urls = [];
              const seen = new Set();
              const push = (url, alt = null, width = null, height = null) => {
                if (!url || seen.has(url)) return;
                seen.add(url);
                urls.push({ url, alt, width, height });
              };
              const extractUrl = (value) => {
                if (!value) return [];
                const matches = [];
                const regex = /url\\(['"]?([^'")]+)['"]?\\)/g;
                let match;
                while ((match = regex.exec(value)) !== null) {
                  matches.push(match[1]);
                }
                return matches;
              };

              document.querySelectorAll('img, [style], [data-src], [data-lazy-src], [data-original], [data-background], [data-bg], [data-browser-automation-image-src]').forEach((element) => {
                const tagName = element.tagName ? element.tagName.toLowerCase() : '';
                const alt = element.getAttribute && element.getAttribute('alt');
                const width = element.getAttribute && element.getAttribute('width');
                const height = element.getAttribute && element.getAttribute('height');
                const safePush = (value) => {
                  try {
                    push(new URL(value, document.baseURI).href, alt, width ? Number(width) : null, height ? Number(height) : null);
                  } catch (error) {
                    return;
                  }
                };
                const attrs = ['src', 'data-src', 'data-lazy-src', 'data-original', 'data-bg', 'data-background'];
                attrs.push('data-browser-automation-image-src');
                attrs.forEach((attr) => {
                  const value = element.getAttribute && element.getAttribute(attr);
                  if (value) safePush(value);
                });
                const style = element.getAttribute && element.getAttribute('style');
                extractUrl(style).forEach((candidate) => safePush(candidate));
                const computed = window.getComputedStyle ? window.getComputedStyle(element) : null;
                if (computed) {
                  extractUrl(computed.backgroundImage || '').forEach((candidate) => safePush(candidate));
                }
                if (tagName === 'img') {
                  const src = element.currentSrc || element.getAttribute && element.getAttribute('src');
                  if (src) safePush(src);
                }
              });

              return urls;
            }
            """
        )
    except Exception:  # pragma: no cover - runtime fallback
        result = []

    if isinstance(result, list):
        live_entries = [entry for entry in result if isinstance(entry, dict)]

    images: list[ExtractedImage] = []
    seen: set[str] = set()
    for entry in live_entries:
        image = _normalize_live_image_entry(entry, base_url)
        if image is None or image.url in seen:
            continue
        seen.add(image.url)
        images.append(image)

    return images


def collect_rendered_images(page: object, base_url: str) -> list[ExtractedImage]:
    try:
        page.evaluate(
            """
            async () => {
              const totalHeight = Math.max(
                document.body?.scrollHeight || 0,
                document.documentElement?.scrollHeight || 0
              );
              const viewportHeight = window.innerHeight || document.documentElement?.clientHeight || 800;
              const step = Math.max(Math.floor(viewportHeight * 0.8), 400);
              const positions = [];
              for (let y = 0; y <= totalHeight; y += step) {
                positions.push(y);
              }
              for (const y of positions) {
                window.scrollTo(0, y);
                await new Promise((resolve) => setTimeout(resolve, 250));
              }
              window.scrollTo(0, 0);
              await new Promise((resolve) => setTimeout(resolve, 250));
            }
            """
        )
    except Exception:  # pragma: no cover - best-effort scrolling
        pass

    return extract_images_from_page(page, base_url)


def annotate_background_images(page: object) -> None:
    try:
        page.evaluate(
            """
            () => {
              const extractUrl = (value) => {
                if (!value) return [];
                const matches = [];
                const regex = /url\\(['"]?([^'")]+)['"]?\\)/g;
                let match;
                while ((match = regex.exec(value)) !== null) {
                  matches.push(match[1]);
                }
                return matches;
              };

              document.querySelectorAll('[role="img"], [data-ux="Background"]').forEach((element) => {
                if (element.querySelector && element.querySelector('img')) return;
                const computed = window.getComputedStyle ? window.getComputedStyle(element) : null;
                const candidates = [
                  ...(extractUrl(element.getAttribute && element.getAttribute('style'))),
                  ...(computed ? extractUrl(computed.backgroundImage || '') : []),
                ];
                const source = candidates.find(Boolean);
                if (!source) return;
                try {
                  const resolved = new URL(source, document.baseURI).href;
                  element.setAttribute('data-browser-automation-image-src', resolved);
                  const alt = element.getAttribute && (element.getAttribute('aria-label') || element.getAttribute('alt'));
                  if (alt) element.setAttribute('data-browser-automation-image-alt', alt);
                } catch (error) {
                  return;
                }
              });
            }
            """
        )
    except Exception:  # pragma: no cover - best-effort browser annotation
        pass
