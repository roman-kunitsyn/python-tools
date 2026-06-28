from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from browser_automation import __version__
from browser_automation.browser import BrowserManager
from browser_automation.cli.parser import build_parser
from browser_automation.config import BrowserAutomationConfig
from browser_automation.crawler import CrawlOptions, crawl_site
from browser_automation.errors import BrowserAutomationError
from browser_automation.exporter import (
    export_crawled_markdown,
    export_html,
    export_images,
    export_links,
    export_markdown,
    export_pdf,
    export_screenshot,
    export_text,
)
from browser_automation.recorder import BrowserRecorder, default_recording_path
from browser_automation.runner import ScenarioRunner
from browser_automation.utils.paths import default_session_dir, page_path_for_url

try:
    from loguru import logger
except ImportError:  # pragma: no cover - runtime dependency fallback
    import logging

    logging.basicConfig(level=logging.INFO)

    class _Logger:
        def debug(self, message: str, *args: object, **kwargs: object) -> None:
            logging.debug(message.format(*args), **kwargs)

        def info(self, message: str, *args: object, **kwargs: object) -> None:
            logging.info(message.format(*args), **kwargs)

        def error(self, message: str, *args: object, **kwargs: object) -> None:
            logging.error(message.format(*args), **kwargs)

    logger = _Logger()


def configure_logging(verbose: bool) -> None:
    if verbose:
        logger.debug("Verbose logging enabled")


def build_config(args: argparse.Namespace) -> BrowserAutomationConfig:
    return BrowserAutomationConfig.from_args(
        config_file=getattr(args, "config", None),
        headless=getattr(args, "headless", None),
        timeout=getattr(args, "timeout", None),
        browser=getattr(args, "browser", None),
        viewport_width=getattr(args, "viewport_width", None),
        viewport_height=getattr(args, "viewport_height", None),
        slow_mo=getattr(args, "slow_mo", None),
        output_dir=getattr(args, "output_dir", None),
    )


def _load_variables(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return json.loads(path.read_text())


def _default_output_dir(config: BrowserAutomationConfig, override: Path | None, *, site_url: str | None = None) -> Path:
    return default_session_dir(override or config.output_dir, site_url=site_url)


def run_record(args: argparse.Namespace, config: BrowserAutomationConfig) -> int:
    output_dir = _default_output_dir(config, getattr(args, "output_dir", None), site_url=args.url)
    output_path = args.output or default_recording_path(args.url, output_dir)
    recorder = BrowserRecorder(browser=config.browser, target=args.target)
    result = recorder.record(args.url, output_path)
    logger.info("Scenario saved to {}", result.output_path)
    return result.exit_code


def run_scenario(args: argparse.Namespace, config: BrowserAutomationConfig) -> int:
    browser = BrowserManager(config)
    runner = ScenarioRunner(browser)
    variables = _load_variables(args.variables)
    runner.run_scenario(args.scenario, url=args.url, variables=variables)
    logger.info("Scenario completed: {}", args.scenario)
    return 0


def run_crawl(args: argparse.Namespace, config: BrowserAutomationConfig) -> int:
    browser = BrowserManager(config)
    options = CrawlOptions(
        start_url=args.url,
        max_depth=args.max_depth,
        page_limit=args.page_limit,
        same_domain_only=not args.follow_external,
    )
    result = crawl_site(browser, options)
    output_dir = _default_output_dir(config, getattr(args, "output_dir", None), site_url=args.url)

    if args.markdown:
        artifacts = export_crawled_markdown(
            result,
            output_dir,
            strip_navigation=getattr(args, "strip_navigation", False),
            download_images=True,
        )
        manifest_path = args.output or (output_dir / "crawl.json")
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                [{"url": page.url, "depth": page.depth, "title": page.title} for page in result.pages],
                indent=2,
                ensure_ascii=False,
            )
        )
        logger.info("Crawled {} pages into {} and {}", len(result.pages), manifest_path, output_dir)
        for artifact in artifacts:
            logger.debug("Wrote markdown page {}", artifact.output_path)
        return 0

    output_path = args.output or (output_dir / "crawl.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            [{"url": page.url, "depth": page.depth, "title": page.title} for page in result.pages],
            indent=2,
            ensure_ascii=False,
        )
    )
    logger.info("Crawled {} pages into {}", len(result.pages), output_path)
    return 0


def run_export(args: argparse.Namespace, config: BrowserAutomationConfig, mode: str) -> int:
    browser = BrowserManager(config)
    output_dir = _default_output_dir(config, getattr(args, "output_dir", None), site_url=args.url)

    if mode == "markdown":
        artifact = export_markdown(browser, args.url, output_dir, strip_navigation=args.strip_navigation)
    elif mode == "html":
        artifact = export_html(browser, args.url, output_dir, strip_navigation=args.strip_navigation)
    elif mode == "links":
        artifact = export_links(browser, args.url, output_dir)
    elif mode == "images":
        artifact = export_images(browser, args.url, output_dir)
    elif mode == "pdf":
        output_path = args.output or page_path_for_url(args.url, output_dir, ".pdf")
        artifact = export_pdf(browser, args.url, output_path)
    elif mode == "screenshot":
        output_path = args.output or page_path_for_url(args.url, output_dir, ".png")
        artifact = export_screenshot(
            browser,
            args.url,
            output_path,
            full_page=args.full_page,
            selector=args.selector,
        )
    elif mode == "text":
        artifact = export_text(browser, args.url, output_dir, strip_navigation=getattr(args, "strip_navigation", False))
    else:
        raise BrowserAutomationError(f"Unsupported export mode: {mode}")

    logger.info("Exported {} to {}", args.url, artifact.output_path)
    return 0


def build_runtime_config(args: argparse.Namespace) -> BrowserAutomationConfig:
    return build_config(args)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    config = build_runtime_config(args)
    configure_logging(getattr(args, "verbose", False))

    try:
        if args.command == "record":
            return run_record(args, config)
        if args.command == "run":
            return run_scenario(args, config)
        if args.command == "crawl":
            return run_crawl(args, config)
        if args.command in {"markdown", "html", "links", "images", "pdf", "screenshot"}:
            return run_export(args, config, args.command)
        if args.command == "version":
            print(__version__)
            return 0

        parser.print_help()
        return 1
    except BrowserAutomationError as error:
        logger.error(str(error))
        return 1
    except RuntimeError as error:
        logger.error(str(error))
        return 1
