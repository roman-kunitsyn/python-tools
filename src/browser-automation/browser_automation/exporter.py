from __future__ import annotations

import json
import mimetypes
import urllib.request
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
from browser_automation.models import CrawlResult, ExportArtifact
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


def _download_image(image_url: str, output_path: Path) -> Path:
    ensure_parent(output_path)
    with urllib.request.urlopen(image_url, timeout=30) as response:  # nosec: B310
        output_path.write_bytes(response.read())
    return output_path


def _image_extension(image_url: str, content_type: str | None = None) -> str:
    parsed = urlparse(image_url)
    suffix = Path(parsed.path).suffix
    if suffix:
        return suffix
    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip())
        if guessed:
            return guessed
    return ".img"


def export_crawled_markdown(
    result: CrawlResult,
    output_dir: Path,
    *,
    strip_navigation: bool = False,
    download_images: bool = True,
) -> list[ExportArtifact]:
    pages_dir = output_dir / "pages"
    images_dir = output_dir / "images"
    artifacts: list[ExportArtifact] = []

    for page in result.pages:
        markdown = html_to_markdown(page.html, strip_navigation=strip_navigation)
        page_slug = slugify_url_path(page.url)
        page_output = page_path_for_url(page.url, pages_dir, ".md")
        ensure_parent(page_output)

        if download_images:
            page_image_dir = images_dir / page_slug
            for index, image in enumerate(extract_images(page.html, page.url), start=1):
                parsed = urlparse(image.url)
                image_name = f"image_{index}{_image_extension(image.url)}"
                image_output = page_image_dir / image_name
                _download_image(image.url, image_output)
                relative_image_path = Path("..") / "images" / page_slug / image_name
                markdown = markdown.replace(image.url, relative_image_path.as_posix())
                if parsed.scheme:
                    markdown = markdown.replace(parsed.geturl(), relative_image_path.as_posix())

        page_output.write_text(markdown)
        artifacts.append(ExportArtifact(source_url=page.url, output_path=page_output))

    return artifacts
