# Browser Automation Tool - Implementation Task

## Overview

Implement a reusable **Browser Automation** CLI tool based on **Python** and **Microsoft Playwright**.

The tool is intended to become part of the internal Python tools collection and provide a unified interface for browser automation, website crawling, content extraction, screenshots, PDF generation, and scenario execution.

The implementation must be modular, extensible, and suitable for future AI Agent integration.

---

# Technology Stack

- Python 3.12+
- uv
- Playwright (Python)
- argparse
- pathlib
- pydantic
- loguru
- beautifulsoup4
- markdownify
- lxml

Optional future support:

- Textual
- FastAPI
- LangGraph

---

# Project Goals

The tool should allow users to:

- automate browsers
- record browser interactions
- execute automation scenarios
- crawl websites
- export website content
- generate screenshots
- generate PDFs
- extract structured data
- integrate with AI agents

The project should expose a clean CLI while keeping all browser logic reusable as a Python library.

---

# Project Structure

```
browser-automation/

├── README.md
├── pyproject.toml

├── src/
│   └── browser_automation/
│
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│
│       ├── browser.py
│       ├── recorder.py
│       ├── runner.py
│       ├── crawler.py
│       ├── exporter.py
│
│       ├── actions/
│       │     click.py
│       │     fill.py
│       │     wait.py
│       │     screenshot.py
│       │     pdf.py
│       │
│       ├── extractors/
│       │     markdown.py
│       │     html.py
│       │     text.py
│       │     links.py
│       │     images.py
│       │
│       ├── scenarios/
│       │
│       ├── models/
│       │
│       ├── utils/
│       │
│       └── templates/
│
└── tests/
```

---

# CLI

```
browser-automation

browser-automation record

browser-automation run

browser-automation crawl

browser-automation screenshot

browser-automation pdf

browser-automation markdown

browser-automation html

browser-automation links

browser-automation images

browser-automation version
```

---

# Configuration

Support configuration using

```
--config config.json
```

Example

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

---

# Record Mode

Implement

```
browser-automation record
```

Responsibilities:

- launch Playwright Codegen
- allow user interaction
- generate initial Playwright script
- save generated scenario
- support Python output

Future support:

- export scenario metadata
- export screenshots
- export DOM snapshots

---

# Run Mode

```
browser-automation run
```

Responsibilities

- execute Playwright scenarios
- pass variables
- capture logs
- capture screenshots on failure
- return exit code

Example

```
browser-automation run \
    --scenario login.py \
    --variables credentials.json
```

---

# Crawl Mode

```
browser-automation crawl
```

Responsibilities

- recursively visit internal pages
- configurable maximum depth
- configurable page limit
- avoid duplicate pages
- respect robots.txt (optional)
- optional sitemap.xml support
- export URL list

---

# Markdown Export

```
browser-automation markdown
```

Responsibilities

- download rendered HTML
- remove scripts/styles
- optionally remove navigation/header/footer
- convert HTML to Markdown
- preserve headings
- preserve tables
- preserve links
- preserve images (optional)

Output

```
docs/

index.md

about.md

products/item-a.md
```

---

# HTML Export

Export cleaned HTML.

---

# Screenshot Mode

```
browser-automation screenshot
```

Support

- full page
- viewport
- element screenshot
- PNG

---

# PDF Export

Generate printable PDF.

---

# Links Extraction

Extract

- internal links
- external links

Export

```
links.json
```

---

# Image Extraction

Export

- image URLs
- alt text
- dimensions (if available)

---

# Browser Abstraction

Create reusable browser manager.

Responsibilities

- launch browser
- open pages
- context management
- authentication
- cookies
- downloads

No browser logic should exist inside CLI commands.

---

# Logging

Use Loguru.

Support

- INFO
- DEBUG
- ERROR

Optional

```
--verbose
```

---

# Error Handling

Handle

- timeout
- network failure
- invalid selectors
- browser crash
- invalid URL

Meaningful error messages are required.

---

# Extensibility

The architecture must allow future implementation of:

- FastAPI server
- AI Agent integration
- Textual UI
- scheduled automation
- remote browsers
- browser pools
- authenticated sessions
- reusable workflows
- browser recording database

---

# Future AI Integration

The architecture should allow AI agents to invoke operations such as

```
crawl(url)

extract_markdown(url)

take_screenshot(url)

run_scenario(name)

export_pdf(url)
```

without knowing Playwright internals.

---

# Coding Guidelines

- modular architecture
- small focused modules
- dependency injection where appropriate
- no global mutable state
- typed Python
- dataclasses or Pydantic models
- pure utility functions when possible
- comprehensive docstrings
- unit-testable design

---

# Deliverables

- Complete CLI implementation
- Modular architecture
- Documentation
- Configuration support
- Example scenarios
- Example configuration
- Unit tests
- README with usage examples
- Ready for future FastAPI and AI Agent integration

This scope is intentionally focused on building a **foundation**, not just a wrapper around Playwright. The resulting tool should become a reusable browser automation platform that other projects (Next.js applications, LangGraph agents, Telegram bots, or batch jobs) can build upon without duplicating browser logic.
