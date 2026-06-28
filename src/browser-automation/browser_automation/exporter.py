from __future__ import annotations

import json
from pathlib import Path

from browser_automation.actions.pdf import pdf as write_pdf
from browser_automation.actions.screenshot import screenshot as write_screenshot
from browser_automation.browser import BrowserManager
from browser_automation.extractors.html import clean_html
from browser_automation.extractors.images import extract_images
from browser_automation.extractors.links import extract_links
from browser_automation.extractors.markdown import html_to_markdown
from browser_automation.extractors.text import extract_text
from browser_automation.models import ExportArtifact
from browser_automation.utils.paths import ensure_parent, page_path_for_url


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
