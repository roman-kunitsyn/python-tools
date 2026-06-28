from __future__ import annotations

import json
import mimetypes
import re
import urllib.request
from urllib.error import URLError
from pathlib import Path
from urllib.parse import urljoin, urlparse

from browser_automation.actions.pdf import pdf as write_pdf
from browser_automation.actions.screenshot import screenshot as write_screenshot
from browser_automation.browser import BrowserManager
from browser_automation.extractors.html import clean_html
from browser_automation.extractors.images import extract_images
from browser_automation.extractors.links import extract_links
from browser_automation.extractors.markdown import html_to_markdown
from browser_automation.extractors.text import extract_text
from browser_automation.models import CrawlResult, ExportArtifact, PageImageManifest
from browser_automation.utils.paths import ensure_parent, page_path_for_url, slugify_url_path


def _fetch_html(browser: BrowserManager, url: str) -> tuple[object, str]:
    with browser.session() as session:
        page = session.open_page(url)
        return page, page.content()


def export_html(browser: BrowserManager, url: str, output_dir: Path, *, strip_navigation: bool = False) -> ExportArtifact:
    _, html = _fetch_html(browser, url)
    output_path = page_path_for_url(url, output_dir, ".html")
    ensure_parent(output_path)
    output_path.write_text(clean_html(html, strip_navigation=strip_navigation))
    return ExportArtifact(source_url=url, output_path=output_path)


def export_markdown(browser: BrowserManager, url: str, output_dir: Path, *, strip_navigation: bool = False) -> ExportArtifact:
    _, html = _fetch_html(browser, url)
    output_path = page_path_for_url(url, output_dir, ".md")
    ensure_parent(output_path)
    output_path.write_text(html_to_markdown(html, strip_navigation=strip_navigation))
    return ExportArtifact(source_url=url, output_path=output_path)


def export_text(browser: BrowserManager, url: str, output_dir: Path, *, strip_navigation: bool = False) -> ExportArtifact:
    _, html = _fetch_html(browser, url)
    output_path = page_path_for_url(url, output_dir, ".txt")
    ensure_parent(output_path)
    output_path.write_text(extract_text(html, strip_navigation=strip_navigation))
    return ExportArtifact(source_url=url, output_path=output_path)


def export_links(browser: BrowserManager, url: str, output_dir: Path) -> ExportArtifact:
    _, html = _fetch_html(browser, url)
    output_path = page_path_for_url(url, output_dir, ".links.json")
    ensure_parent(output_path)
    data = [
        {"url": link.url, "text": link.text, "is_internal": link.is_internal}
        for link in extract_links(html, url)
    ]
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return ExportArtifact(source_url=url, output_path=output_path)


def export_images(browser: BrowserManager, url: str, output_dir: Path) -> ExportArtifact:
    _, html = _fetch_html(browser, url)
    output_path = page_path_for_url(url, output_dir, ".images.json")
    ensure_parent(output_path)
    data = [
        {"url": image.url, "alt": image.alt, "width": image.width, "height": image.height}
        for image in extract_images(html, url)
    ]
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return ExportArtifact(source_url=url, output_path=output_path)


def export_screenshot(
    browser: BrowserManager,
    url: str,
    output_path: Path,
    *,
    full_page: bool = True,
    selector: str | None = None,
) -> ExportArtifact:
    with browser.session() as session:
        page = session.open_page(url)
        write_screenshot(page, output_path, full_page=full_page, selector=selector)
    return ExportArtifact(source_url=url, output_path=output_path)


def export_pdf(browser: BrowserManager, url: str, output_path: Path) -> ExportArtifact:
    with browser.session() as session:
        page = session.open_page(url)
        write_pdf(page, output_path)
    return ExportArtifact(source_url=url, output_path=output_path)


def _download_image(image_url: str, output_path: Path) -> tuple[Path, str | None]:
    ensure_parent(output_path)
    parsed = urlparse(image_url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Unsupported image URL: {image_url!r}")

    try:
        with urllib.request.urlopen(image_url, timeout=30) as response:  # nosec: B310
            content_type = response.headers.get_content_type()
            output_path.write_bytes(response.read())
        return output_path, content_type
    except URLError as error:
        raise RuntimeError(f"Failed to download image {image_url!r}: {error}") from error


def _image_extension(image_url: str, content_type: str | None = None) -> str:
    parsed = urlparse(image_url)
    match = re.search(r"\.(png|jpe?g|gif|webp|avif|bmp|svg)(?=$|[/?#])", parsed.path, flags=re.IGNORECASE)
    if match:
        suffix = f".{match.group(1).lower()}"
        if suffix == ".jpeg":
            return ".jpg"
        return suffix
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
        if guessed:
            if guessed.lower() == ".jpe":
                return ".jpg"
            return guessed
    return ".png"


_MARKDOWN_IMAGE_PATTERN = re.compile(r"(!\[[^\]]*?\]\()([^)]+)(\))")
_HTML_IMAGE_PATTERN = re.compile(r'(<img\b[^>]*?\bsrc=["\'])([^"\']+)(["\'])', flags=re.IGNORECASE)
_PLACEHOLDER_GIF_PREFIXES = {
    "data:image/gif;base64,r0lgodlhaqabaad",
    "data:image/gif;base64,r0lgodlh",
}


def _normalized_image_key(url: str, *, page_url: str | None = None) -> tuple[str, str, str, str] | None:
    candidate = url.strip().strip("<>")
    if candidate.startswith("data:"):
        return None
    if page_url is not None:
        candidate = urljoin(page_url, candidate)
    parsed = urlparse(candidate)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    return (parsed.netloc, parsed.path, parsed.query, parsed.fragment)


def _build_image_replacements(page_url: str, page_images: list[object], page_slug: str, page_image_dir: Path) -> tuple[dict[tuple[str, str, str, str], str], list[tuple[str, str]]]:
    replacements: dict[tuple[str, str, str, str], str] = {}
    downloaded_images: list[tuple[str, str]] = []

    for index, image in enumerate(page_images, start=1):
        temp_image_output = page_image_dir / f"image_{index}"
        try:
            image_output, content_type = _download_image(image.url, temp_image_output)
        except (ValueError, RuntimeError):
            continue

        final_extension = _image_extension(image.url, content_type)
        if image_output.suffix != final_extension:
            final_path = image_output.with_suffix(final_extension)
            image_output.replace(final_path)
            image_output = final_path

        relative_image_path = Path("..") / "images" / page_slug / image_output.name
        local_path = relative_image_path.as_posix()
        downloaded_images.append((image.url, local_path))

        source_keys = {
            _normalized_image_key(image.url),
            _normalized_image_key(image.url, page_url=page_url),
        }
        for key in source_keys:
            if key is not None:
                replacements[key] = local_path

    return replacements, downloaded_images


def _rewrite_markdown_image_references(markdown: str, replacements: dict[tuple[str, str, str, str], str], *, page_url: str) -> str:
    def replace_markdown_image(match: re.Match[str]) -> str:
        prefix, raw_url, suffix = match.groups()
        candidate = raw_url.strip()
        if candidate.lower().startswith(tuple(_PLACEHOLDER_GIF_PREFIXES)):
            return ""

        normalized = _normalized_image_key(candidate, page_url=page_url)
        local_path = replacements.get(normalized) if normalized is not None else None
        if local_path is None:
            return match.group(0)
        return f"{prefix}{local_path}{suffix}"

    def replace_html_image(match: re.Match[str]) -> str:
        prefix, raw_url, suffix = match.groups()
        candidate = raw_url.strip()
        normalized = _normalized_image_key(candidate, page_url=page_url)
        local_path = replacements.get(normalized) if normalized is not None else None
        if local_path is None:
            return match.group(0)
        return f"{prefix}{local_path}{suffix}"

    rewritten = _MARKDOWN_IMAGE_PATTERN.sub(replace_markdown_image, markdown)
    rewritten = _HTML_IMAGE_PATTERN.sub(replace_html_image, rewritten)
    return rewritten


def _rewrite_html_image_references(html: str, downloaded_images: list[tuple[str, str]], *, page_url: str) -> str:
    rewritten = html
    for source_url, local_path in downloaded_images:
        parsed = urlparse(source_url)
        candidate_urls = {
            source_url,
            f"//{parsed.netloc}{parsed.path}" if parsed.netloc else source_url,
            urljoin(page_url, source_url),
        }
        for candidate in candidate_urls:
            if candidate:
                rewritten = rewritten.replace(candidate, local_path)
    return rewritten


def _is_placeholder_image(image_url: str) -> bool:
    normalized = image_url.strip().lower()
    return normalized.startswith("data:image/gif;base64,r0lgodlh")


def export_crawled_markdown(
    result: CrawlResult,
    output_dir: Path,
    *,
    strip_navigation: bool = False,
    download_images: bool = True,
) -> list[ExportArtifact]:
    pages_dir = output_dir / "pages"
    images_dir = output_dir / "images"
    manifests_dir = output_dir / "manifests"
    images_index_path = output_dir / "images.json"
    artifacts: list[ExportArtifact] = []
    images_index: list[dict[str, object]] = []

    for page in result.pages:
        markdown = html_to_markdown(page.html, strip_navigation=strip_navigation)
        page_slug = slugify_url_path(page.url)
        page_output = page_path_for_url(page.url, pages_dir, ".md")
        manifest_output = page_path_for_url(page.url, manifests_dir, ".json")
        ensure_parent(page_output)
        ensure_parent(manifest_output)

        if download_images:
            page_image_dir = images_dir / page_slug
            page_images = [image for image in (page.images or extract_images(page.html, page.url)) if not _is_placeholder_image(image.url)]
            manifest = PageImageManifest(
                page_url=page.url,
                page_title=page.title,
                page_depth=page.depth,
                page_markdown=page_output,
                images=page_images,
            )
            manifest_output.write_text(
                json.dumps(
                    {
                        "page_url": manifest.page_url,
                        "page_title": manifest.page_title,
                        "page_depth": manifest.page_depth,
                        "page_markdown": str(manifest.page_markdown),
                        "images": [
                            {
                                "url": image.url,
                                "alt": image.alt,
                                "width": image.width,
                                "height": image.height,
                            }
                            for image in manifest.images
                        ],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
            images_index.extend(
                {
                    "page_url": page.url,
                    "page_title": page.title,
                    "page_depth": page.depth,
                    "page_markdown": str(page_output),
                    "image_url": image.url,
                    "image_alt": image.alt,
                    "image_width": image.width,
                    "image_height": image.height,
                }
                for image in page_images
            )
            image_replacements, downloaded_images = _build_image_replacements(page.url, page_images, page_slug, page_image_dir)
            rewritten_html = _rewrite_html_image_references(page.html, downloaded_images, page_url=page.url)
            markdown = html_to_markdown(rewritten_html, strip_navigation=strip_navigation)
            markdown = _rewrite_markdown_image_references(markdown, image_replacements, page_url=page.url)

        page_output.write_text(markdown)
        artifacts.append(ExportArtifact(source_url=page.url, output_path=page_output))
        artifacts.append(ExportArtifact(source_url=page.url, output_path=manifest_output))

    ensure_parent(images_index_path)
    images_index_path.write_text(json.dumps(images_index, indent=2, ensure_ascii=False))
    artifacts.append(ExportArtifact(source_url=result.root_url, output_path=images_index_path))

    return artifacts
