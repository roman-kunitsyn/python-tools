from __future__ import annotations

import json
import mimetypes
import re
import urllib.request
from urllib.error import URLError
from pathlib import Path
from urllib.parse import urlparse

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
    artifacts: list[ExportArtifact] = []

    for page in result.pages:
        markdown = html_to_markdown(page.html, strip_navigation=strip_navigation)
        page_slug = slugify_url_path(page.url)
        page_output = page_path_for_url(page.url, pages_dir, ".md")
        manifest_output = page_path_for_url(page.url, manifests_dir, ".json")
        ensure_parent(page_output)
        ensure_parent(manifest_output)

        if download_images:
            page_image_dir = images_dir / page_slug
            page_images = page.images or extract_images(page.html, page.url)
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
                image_name = image_output.name
                relative_image_path = Path("..") / "images" / page_slug / image_name
                markdown = markdown.replace(image.url, relative_image_path.as_posix())

        page_output.write_text(markdown)
        artifacts.append(ExportArtifact(source_url=page.url, output_path=page_output))
        artifacts.append(ExportArtifact(source_url=page.url, output_path=manifest_output))

    return artifacts
