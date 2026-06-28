from __future__ import annotations

import argparse
from pathlib import Path


def add_shared_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", type=Path, help="Load defaults from a JSON config file.")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=None, help="Run browsers headless.")
    parser.add_argument("--timeout", type=int, default=None, help="Navigation and action timeout in milliseconds.")
    parser.add_argument(
        "--browser",
        choices=("chromium", "firefox", "webkit"),
        default=None,
        help="Browser engine to launch.",
    )
    parser.add_argument("--viewport-width", type=int, default=None, help="Viewport width in pixels.")
    parser.add_argument("--viewport-height", type=int, default=None, help="Viewport height in pixels.")
    parser.add_argument("--slow-mo", type=int, default=None, help="Slow down actions in milliseconds.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated artifacts. Defaults to logs/browser-automation/{timestamp}.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="browser-automation", description="Browser automation and export utilities.")
    add_shared_arguments(parser)

    subparsers = parser.add_subparsers(dest="command")

    record = subparsers.add_parser("record", help="Launch Playwright codegen and save a Python scenario.")
    record.add_argument("url", nargs="?", help="Optional URL to open before recording.")
    record.add_argument("--output", type=Path, default=None, help="Scenario file path.")
    record.add_argument("--target", default="python", choices=("python",), help="Scenario output language.")
    record.add_argument("--browser", choices=("chromium", "firefox", "webkit"), default=None, help=argparse.SUPPRESS)

    run = subparsers.add_parser("run", help="Execute a Python scenario against a browser.")
    run.add_argument("--scenario", type=Path, required=True, help="Scenario Python file.")
    run.add_argument("--url", help="Optional starting URL.")
    run.add_argument("--variables", type=Path, help="JSON file containing scenario variables.")
    run.add_argument("--browser", choices=("chromium", "firefox", "webkit"), default=None, help=argparse.SUPPRESS)

    crawl = subparsers.add_parser("crawl", help="Recursively crawl internal pages.")
    crawl.add_argument("url", help="Root URL to crawl.")
    crawl.add_argument("--max-depth", type=int, default=2, help="Maximum crawl depth.")
    crawl.add_argument("--page-limit", type=int, default=50, help="Maximum number of pages to visit.")
    crawl.add_argument("--follow-external", action="store_true", help="Allow links to leave the starting host.")
    crawl.add_argument("--output", type=Path, default=None, help="Output JSON file for the URL list.")
    crawl.add_argument(
        "--markdown",
        action="store_true",
        help="Save crawled pages as Markdown in the session folder and download images there too.",
    )

    screenshot = subparsers.add_parser("screenshot", help="Capture a page or element screenshot.")
    screenshot.add_argument("url", help="Page URL to capture.")
    screenshot.add_argument("--output", type=Path, default=None, help="PNG output file.")
    screenshot.add_argument("--selector", default=None, help="Optional CSS selector to capture.")
    screenshot.add_argument("--full-page", action="store_true", help="Capture the full page.")

    pdf = subparsers.add_parser("pdf", help="Export a page to PDF.")
    pdf.add_argument("url", help="Page URL to export.")
    pdf.add_argument("--output", type=Path, default=None, help="PDF output file.")

    markdown = subparsers.add_parser("markdown", help="Export a cleaned page to Markdown.")
    markdown.add_argument("url", help="Page URL to export.")
    markdown.add_argument("--output-dir", type=Path, default=None, help="Directory for exported Markdown files.")
    markdown.add_argument("--strip-navigation", action="store_true", help="Remove nav/header/footer content.")

    html = subparsers.add_parser("html", help="Export a cleaned page to HTML.")
    html.add_argument("url", help="Page URL to export.")
    html.add_argument("--output-dir", type=Path, default=None, help="Directory for exported HTML files.")
    html.add_argument("--strip-navigation", action="store_true", help="Remove nav/header/footer content.")

    links = subparsers.add_parser("links", help="Export page links as JSON.")
    links.add_argument("url", help="Page URL to export.")
    links.add_argument("--output-dir", type=Path, default=None, help="Directory for exported JSON files.")

    images = subparsers.add_parser("images", help="Export page images as JSON.")
    images.add_argument("url", help="Page URL to export.")
    images.add_argument("--output-dir", type=Path, default=None, help="Directory for exported JSON files.")

    subparsers.add_parser("version", help="Show the tool version.")

    return parser
