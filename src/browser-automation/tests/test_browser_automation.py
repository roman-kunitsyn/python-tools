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
from browser_automation.extractors.images import extract_images_from_page
from browser_automation.extractors.links import extract_links
from browser_automation.extractors.markdown import html_to_markdown
from browser_automation.extractors.text import extract_text
from browser_automation.exporter import _image_extension
from browser_automation.utils.paths import default_session_dir, page_path_for_url


class FakePage:
    def __init__(self, url: str, html: str, live_images: list[dict[str, object]] | None = None) -> None:
        self._url = url
        self._html = html
        self._live_images = live_images or []

    def goto(self, url: str, timeout: int | None = None, wait_until: str | None = None) -> None:
        self._url = url

    def content(self) -> str:
        return self._html

    def title(self) -> str:
        return "Example"

    def evaluate(self, script: str):
        return self._live_images


class FakeSession:
    def __init__(self, pages: dict[str, str | dict[str, object]]) -> None:
        self._pages = pages
        self.context = self
        self.browser = self

    def new_page(self) -> FakePage:
        return FakePage("", "")

    def open_page(self, url: str | None = None) -> FakePage:
        entry = self._pages.get(url or "", self._pages.get("default", ""))
        if isinstance(entry, dict):
            return FakePage(
                url or "",
                str(entry.get("html", "")),
                live_images=list(entry.get("live_images", [])),
            )
        return FakePage(url or "", str(entry))


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

    def test_default_session_dir_uses_site_name_and_timestamp(self) -> None:
        session_dir = default_session_dir(now=datetime(2026, 6, 28, 10, 57, 24), site_url="https://boat-rental-samui.com/")
        self.assertEqual(session_dir, Path("logs") / "browser-automation" / "boat_rental_samui-2026_06_28-10_57_24")

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
              <img data-src="https://img1.wsimg.com/example/photo.jpeg" alt="Lazy" />
              <div style="background-image: url('https://cdn.example.com/banner.jpg')"></div>
              <picture>
                <source srcset="/small.png 1x, /large.png 2x" />
              </picture>
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
        self.assertEqual(len(images), 5)
        self.assertEqual(images[0].alt, "Hero")
        self.assertEqual(images[0].width, 640)
        self.assertEqual(images[0].height, 480)
        self.assertTrue(any(image.url == "https://img1.wsimg.com/example/photo.jpeg" for image in images))
        self.assertTrue(any(image.url == "https://cdn.example.com/banner.jpg" for image in images))
        self.assertTrue(any(image.url.endswith("/small.png") for image in images))
        self.assertTrue(any(image.url.endswith("/large.png") for image in images))

        markdown = html_to_markdown(html, strip_navigation=True)
        self.assertIn("Landing", markdown)
        self.assertIn("About", markdown)

    def test_extract_images_from_live_page(self) -> None:
        page = FakePage(
            "https://example.com/",
            "<html><body><img src='/fallback.png' alt='Fallback' /></body></html>",
            live_images=[
                {"url": "/live.png", "alt": "Live", "width": 128, "height": 64},
                {"url": "https://cdn.example.com/banner.jpg", "alt": "Banner", "width": None, "height": None},
            ],
        )

        images = extract_images_from_page(page, "https://example.com/")

        self.assertEqual(len(images), 2)
        self.assertEqual(images[0].url, "https://example.com/live.png")
        self.assertEqual(images[0].alt, "Live")
        self.assertEqual(images[0].width, 128)
        self.assertEqual(images[1].url, "https://cdn.example.com/banner.jpg")

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

    def test_image_extension_handles_transformed_jpeg_urls(self) -> None:
        image_url = (
            "https://img1.wsimg.com/isteam/ip/8705e31a-681a-4b03-a1ff-b2bbf21bc4d0/"
            "WhatsApp%20Image%202026-06-02%20at%2012.54.22.jpeg/:/cr=t:17.94%25,l:0%25,w:100%25,h:64.13%25/"
            "rs=w:720,h:541,cg:true"
        )
        self.assertEqual(_image_extension(image_url), ".jpg")

    def test_crawl_markdown_writes_pages_and_images(self) -> None:
        html = """
        <html><body>
          <h1>Landing</h1>
          <p>Hello <a href="/about">About</a></p>
          <img src="https://example.com/assets/hero.png" alt="Hero" />
        </body></html>
        """
        pages = {
            "https://example.com/": {"html": html, "live_images": []},
            "https://example.com/about": "<html><body><p>About</p></body></html>",
        }
        result = crawl_site(FakeBrowserManager(pages), CrawlOptions(start_url="https://example.com/", max_depth=1, page_limit=10))

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            def fake_download(image_url: str, output_path: Path) -> tuple[Path, str]:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text("image-bytes")
                return output_path, "image/png"

            from browser_automation import exporter as exporter_module

            original_download = exporter_module._download_image
            exporter_module._download_image = fake_download
            try:
                artifacts = export_crawled_markdown(result, output_dir)
            finally:
                exporter_module._download_image = original_download

            markdown_artifacts = [artifact for artifact in artifacts if artifact.output_path.suffix == ".md"]
            manifest_artifacts = [artifact for artifact in artifacts if artifact.output_path.suffix == ".json"]
            self.assertEqual(len(markdown_artifacts), 2)
            self.assertEqual(len(manifest_artifacts), 2)
            landing_page = output_dir / "pages" / "index.md"
            about_page = output_dir / "pages" / "about.md"
            image_file = output_dir / "images" / "index" / "image_1.png"
            manifest_file = output_dir / "manifests" / "index.json"

            self.assertTrue(landing_page.exists())
            self.assertTrue(about_page.exists())
            self.assertTrue(image_file.exists())
            self.assertTrue(manifest_file.exists())
            self.assertIn("../images/index/image_1.png", landing_page.read_text())
            manifest = json.loads(manifest_file.read_text())
            self.assertEqual(manifest["page_url"], "https://example.com/")
            self.assertEqual(len(manifest["images"]), 1)
            self.assertEqual(manifest["images"][0]["url"], "https://example.com/assets/hero.png")

    def test_crawl_site_collects_live_dom_images(self) -> None:
        html = "<html><body><img src='/fallback.png' alt='Fallback' /></body></html>"
        pages = {
            "https://example.com/": {
                "html": html,
                "live_images": [
                    {"url": "/live.png", "alt": "Live", "width": 128, "height": 64},
                    {"url": "https://img1.wsimg.com/example/photo.jpeg", "alt": "External", "width": None, "height": None},
                ],
            }
        }

        result = crawl_site(
            FakeBrowserManager(pages),
            CrawlOptions(start_url="https://example.com/", max_depth=0, page_limit=10),
        )

        self.assertEqual(len(result.pages), 1)
        self.assertEqual([image.url for image in result.pages[0].images], [
            "https://example.com/live.png",
            "https://img1.wsimg.com/example/photo.jpeg",
        ])


if __name__ == "__main__":
    unittest.main()
