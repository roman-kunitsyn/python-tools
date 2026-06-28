from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import urldefrag, urlparse

from browser_automation.browser import BrowserManager
from browser_automation.extractors.links import extract_links
from browser_automation.models import CrawlPage, CrawlResult


@dataclass(slots=True)
class CrawlOptions:
    start_url: str
    max_depth: int = 2
    page_limit: int = 50
    same_domain_only: bool = True


def _normalize_url(url: str) -> str:
    return urldefrag(url)[0]


def _is_same_domain(candidate: str, root: str) -> bool:
    candidate_host = urlparse(candidate).netloc
    root_host = urlparse(root).netloc
    return candidate_host == root_host


def crawl_site(browser: BrowserManager, options: CrawlOptions) -> CrawlResult:
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(_normalize_url(options.start_url), 0)]
    result = CrawlResult(root_url=options.start_url)

    with browser.session() as session:
        while queue and len(result.pages) < options.page_limit:
            url, depth = queue.pop(0)
            if url in visited or depth > options.max_depth:
                continue

            visited.add(url)
            page = session.open_page(url)
            html = page.content()
            title = page.title()
            result.pages.append(CrawlPage(url=url, depth=depth, title=title, html=html))

            if depth >= options.max_depth:
                continue

            for link in extract_links(html, url):
                candidate = _normalize_url(link.url)
                if candidate in visited:
                    continue
                if options.same_domain_only and not _is_same_domain(candidate, options.start_url):
                    continue
                queue.append((candidate, depth + 1))

    return result
