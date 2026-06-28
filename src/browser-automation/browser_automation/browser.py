from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from browser_automation.config import BrowserAutomationConfig

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - runtime dependency fallback
    sync_playwright = None


@dataclass(slots=True)
class BrowserSession:
    playwright: Any
    browser: Any
    context: Any
    config: BrowserAutomationConfig

    def open_page(self, url: str | None = None) -> Any:
        page = self.context.new_page()
        if url is not None:
            page.goto(url, timeout=self.config.timeout, wait_until="domcontentloaded")
        return page


class BrowserManager:
    def __init__(self, config: BrowserAutomationConfig) -> None:
        self.config = config

    @contextmanager
    def session(self) -> Iterator[BrowserSession]:
        if sync_playwright is None:
            raise RuntimeError(
                "Playwright is not installed. Install the browser automation dependencies to use this command."
            )

        with sync_playwright() as playwright:
            browser_type = getattr(playwright, self.config.browser)
            browser = browser_type.launch(headless=self.config.headless, slow_mo=self.config.slow_mo)
            context = browser.new_context(
                viewport={
                    "width": self.config.viewport.width,
                    "height": self.config.viewport.height,
                }
            )
            try:
                yield BrowserSession(playwright=playwright, browser=browser, context=context, config=self.config)
            finally:
                context.close()
                browser.close()
