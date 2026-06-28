from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from browser_automation.browser import BrowserManager
from browser_automation.config import BrowserAutomationConfig
from browser_automation.crawler import CrawlOptions, crawl_site
from browser_automation.exporter import export_crawled_markdown
from browser_automation.extractors.html import clean_html
from browser_automation.extractors.images import extract_images
from browser_automation.extractors.links import extract_links
from browser_automation.extractors.markdown import html_to_markdown
from browser_automation.extractors.text import extract_text
from browser_automation.utils.paths import default_session_dir, page_path_for_url


class FakePage:
    def __init__(self, url: str, html: str) -> None:
        self._url = url
        self._html = html

    def goto(self, url: str, timeout: int | None = None, wait_until: str | None = None) -> None:
        self._url = url

    def content(self) -> str:
        return self._html

    def title(self) -> str:
        return "Example"


class FakeSession:
    def __init__(self, pages: dict[str, str]) -> None:
        self._pages = pages
        self.context = self
        self.browser = self

    def new_page(self) -> FakePage:
        return FakePage("", "")

    def open_page(self, url: str | None = None) -> FakePage:
        html = self._pages.get(url or "", self._pages.get("default", ""))
        return FakePage(url or "", html)


class FakeBrowserManager:
    def __init__(self, pages: dict[str, str]) -> None:
        self._pages = pages

    @contextmanager
    def session(self):
        yield FakeSession(self._pages)


class BrowserAutomationTests(unittest.TestCase):
    def test_config_merges_file_and_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_file.write_text(
                json.dumps(
                    {
                        "headless": False,
                        "timeout": 10_000,
                        "browser": "firefox",
                        "viewport": {"width": 1024, "height": 768},
                    }
                )
            )

            config = BrowserAutomationConfig.from_args(
                config_file=config_file,
                headless=True,
                timeout=20_000,
                browser="chromium",
                viewport_width=1440,
                viewport_height=900,
                output_dir=Path("exports"),
            )

            self.assertTrue(config.headless)
            self.assertEqual(config.timeout, 20_000)
            self.assertEqual(config.browser, "chromium")
            self.assertEqual(config.viewport.width, 1440)
            self.assertEqual(config.viewport.height, 900)
            self.assertEqual(config.output_dir, Path("exports"))

    def test_default_session_dir_uses_timestamped_browser_automation_root(self) -> None:
        session_dir = default_session_dir(now=datetime(2026, 6, 28, 10, 57, 24))
        self.assertEqual(session_dir, Path("logs") / "browser-automation" / "2026_06_28-10_57_24")

    def test_extractors_handle_html_without_optional_dependencies(self) -> None:
        html = """
        <html>
          <head><title>Example</title><script>bad()</script></head>
          <body>
            <header>Header</header>
            <main>
              <h1>Landing</h1>
              <p>Hello <a href="/about">About</a></p>
              <img src="/hero.png" alt="Hero" width="640" height="480" />
            </main>
          </body>
        </html>
        """

        cleaned = clean_html(html, strip_navigation=True)
        self.assertNotIn("script", cleaned.lower())
        self.assertNotIn("header", cleaned.lower())

        text = extract_text(html, strip_navigation=True)
        self.assertIn("Landing", text)
        self.assertIn("Hello", text)

        links = extract_links(html, "https://example.com/")
        self.assertEqual(len(links), 1)
        self.assertTrue(links[0].is_internal)
        self.assertEqual(links[0].url, "https://example.com/about")

        images = extract_images(html, "https://example.com/")
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0].alt, "Hero")
        self.assertEqual(images[0].width, 640)
        self.assertEqual(images[0].height, 480)

        markdown = html_to_markdown(html, strip_navigation=True)
        self.assertIn("Landing", markdown)
        self.assertIn("About", markdown)

    def test_crawl_site_visits_internal_links_once(self) -> None:
        root_html = """
        <html><body>
          <a href="/about">About</a>
          <a href="https://example.com/contact">Contact</a>
          <a href="https://external.test/">External</a>
        </body></html>
        """
        about_html = """
        <html><body>
          <a href="/about">About</a>
          <a href="/team">Team</a>
        </body></html>
        """
        team_html = "<html><body><p>Team</p></body></html>"
        pages = {
            "https://example.com/": root_html,
            "https://example.com/about": about_html,
            "https://example.com/contact": "<html><body><p>Contact</p></body></html>",
            "https://example.com/team": team_html,
        }

        result = crawl_site(
            FakeBrowserManager(pages),
            CrawlOptions(start_url="https://example.com/", max_depth=2, page_limit=10, same_domain_only=True),
        )

        self.assertEqual(result.root_url, "https://example.com/")
        self.assertEqual(result.urls, ["https://example.com/", "https://example.com/about", "https://example.com/contact", "https://example.com/team"])

    def test_page_path_for_url_uses_index_for_root(self) -> None:
        self.assertEqual(page_path_for_url("https://example.com/", Path("docs"), ".md"), Path("docs/index.md"))
        self.assertEqual(page_path_for_url("https://example.com/products/item-a", Path("docs"), ".md"), Path("docs/products/item-a.md"))

    def test_crawl_markdown_writes_pages_and_images(self) -> None:
        html = """
        <html><body>
          <h1>Landing</h1>
          <p>Hello <a href="/about">About</a></p>
          <img src="https://example.com/assets/hero.png" alt="Hero" />
        </body></html>
        """
        pages = {"https://example.com/": html, "https://example.com/about": "<html><body><p>About</p></body></html>"}
        result = crawl_site(FakeBrowserManager(pages), CrawlOptions(start_url="https://example.com/", max_depth=1, page_limit=10))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            def fake_download(image_url: str, output_path: Path) -> Path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text("image-bytes")
                return output_path

            from browser_automation import exporter as exporter_module

            original_download = exporter_module._download_image
            exporter_module._download_image = fake_download
            try:
                artifacts = export_crawled_markdown(result, output_dir)
            finally:
                exporter_module._download_image = original_download

            self.assertEqual(len(artifacts), 2)
            landing_page = output_dir / "pages" / "index.md"
            about_page = output_dir / "pages" / "about.md"
            image_file = output_dir / "images" / "index" / "image_1.png"

            self.assertTrue(landing_page.exists())
            self.assertTrue(about_page.exists())
            self.assertTrue(image_file.exists())
            self.assertIn("../images/index/image_1.png", landing_page.read_text())


if __name__ == "__main__":
    unittest.main()
