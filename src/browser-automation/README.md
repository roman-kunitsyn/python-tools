# Browser Automation

## Project Overview

`browser-automation` is a reusable browser automation tool built on Python and
Playwright. The module keeps browser logic in a small library layer and exposes
thin CLI entry points for recording scenarios, running scenarios, crawling
sites, and exporting page content.

Implementation status: initial foundation implemented in this directory.

By default, generated files are written to:

```text
./logs/browser-automation/{YYYY_MM_DD-HH_MM_SS}/
```

## Supported Commands

```bash
uv run python src/browser-automation/browser-automation.py --help
uv run python src/browser-automation/browser-automation.py record
uv run python src/browser-automation/browser-automation.py run
uv run python src/browser-automation/browser-automation.py crawl
uv run python src/browser-automation/browser-automation.py screenshot
uv run python src/browser-automation/browser-automation.py pdf
uv run python src/browser-automation/browser-automation.py markdown
uv run python src/browser-automation/browser-automation.py html
uv run python src/browser-automation/browser-automation.py links
uv run python src/browser-automation/browser-automation.py images
uv run python src/browser-automation/browser-automation.py version
```

## Configuration

The CLI accepts a JSON config file:

```bash
uv run python src/browser-automation/browser-automation.py \
  --config config.json \
  markdown https://example.com
```

To crawl and save Markdown pages plus downloaded images into the session
folder:

```bash
uv run python src/browser-automation/browser-automation.py crawl \
  "https://example.com/" \
  --markdown
```

Example config:

```json
{
  "headless": true,
  "timeout": 30000,
  "browser": "chromium",
  "viewport": {
    "width": 1440,
    "height": 900
  }
}
```

## Key Features

- record Playwright scenarios with codegen
- run Python scenario files with variables
- crawl internal pages with depth and page limits
- crawl pages into Markdown and download page images into the session folder
- export rendered HTML, Markdown, links, images, screenshots, and PDFs
- reuse a browser abstraction from other tools or future agents

## Project Structure

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

## Development Notes

- Keep browser logic out of the CLI layer.
- Prefer small, testable helpers for extraction and export logic.
- Treat Playwright and HTML parsing dependencies as runtime capabilities, not
  hard requirements for importing the package.
- Update this README, the implementation plan, and a report whenever behavior
  changes.
