# Browser Automation Implementation Plan

## Module Purpose

`browser-automation` provides a reusable Playwright-based foundation for
recording scenarios, running scenarios, crawling sites, and exporting rendered
content.

The module should remain a browser automation platform, not a one-off script.

## Current Structure

```text
src/browser-automation/
├── README.md
├── browser-automation.py
├── browser_automation/
│   ├── actions/
│   ├── browser.py
│   ├── cli/
│   ├── config.py
│   ├── crawler.py
│   ├── errors.py
│   ├── exporter.py
│   ├── extractors/
│   ├── main.py
│   ├── models/
│   ├── recorder.py
│   ├── runner.py
│   ├── scenarios/
│   ├── templates/
│   └── utils/
├── docs/
│   ├── DEVELOPMENT_GUIDELINE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── reports/
└── tests/
```

## Implemented

- Thin script entry point.
- CLI parser with commands for:
  - `record`
  - `run`
  - `crawl`
  - `screenshot`
  - `pdf`
  - `markdown`
  - `html`
  - `links`
  - `images`
  - `version`
- Pydantic configuration model with JSON config loading and command-line
  overrides.
- Default session output rooted at `./logs/browser-automation/{site}-{timestamp}/`
  for URL-based commands when no output directory is supplied.
- Browser manager abstraction for Playwright sessions and page opening.
- Scenario runner that loads Python scenario files and injects browser context
  objects.
- Recorder wrapper around Playwright codegen.
- Crawl service for recursive internal-page traversal.
- Crawl-to-Markdown export that writes page files and downloads page images
  into the session folder with image extensions resolved to `.png` or `.jpg`
  when possible. Image discovery includes lazy-loaded attributes, `srcset`,
  background-image URLs, external image domains, and live DOM inspection.
- Export helpers for cleaned HTML, Markdown, text, links, images, screenshots,
  and PDFs.
- Example scenario template.

## Partial

- The `record` command wraps Playwright codegen, but the generated scenario
  workflow is still intentionally lightweight.
- Failure screenshots for `run` are not yet automatic.
- Robots.txt and sitemap.xml support are not implemented yet.
- Remote browser and session persistence support are not implemented yet.
- Crawl Markdown export currently downloads images into per-page folders within
  the session root and rewrites image references to local paths.

## Not Started

- FastAPI integration.
- Textual UI.
- Browser pool management.
- Authenticated session storage.
- Crawl persistence and incremental refresh.

## Next Small Parts

1. Add explicit error types and richer command failure reporting.
2. Add tests for the crawler, exporter, and crawl-markdown helpers with
   browser/page fakes.
3. Add optional robots.txt and sitemap.xml discovery.
4. Add scenario failure screenshots and structured run results.

## Documentation Rules

When implementation changes:

1. Update this plan to match the real state.
2. Update `README.md` if user-facing behavior changed.
3. Add a report under `docs/reports/`.
4. Keep the CLI thin and the browser boundary reusable.
