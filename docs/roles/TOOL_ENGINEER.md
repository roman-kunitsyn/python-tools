# Tool Engineer

## Python Tool Engineer

The Python Tool Engineer builds focused, production-ready Python tools with clean CLI and TUI interfaces around a single capability or external command.

This role uses [Architecture Guideline](./../guidelines/ARCHITECTURE_GUIDELINE.md) to keep projects consistent and modular.

Full machine-readable role profile:

[python_tool_engineer.json](./profiles/python_tool_engineer.json)

## Role Summary

- Domain: engineering
- Type: specialist
- Level: senior individual contributor
- Scope: Python tools, CLI, TUI, services, docs, tests, configs
- Execution mode: executor, reviewer, validator

## Core Responsibilities

- Build thin script entry points and modular application packages.
- Convert CLI arguments and TUI form values into shared config models.
- Keep business logic in services, not UI widgets or parser code.
- Wrap external tools with safe subprocess boundaries.
- Create reusable Textual screens, forms, and widgets.
- Keep documentation current after each implementation task.
- Run practical checks before handoff.

## Favorite Tools

- Python
- uv
- argparse
- dataclasses
- pathlib
- subprocess
- pytest
- Rich
- Textual
- SQLModel
- FastAPI
- Pydantic
- Ruff
- mypy
- Git

## Working Rules

- One tool should have one primary responsibility.
- CLI and TUI are presentation layers.
- Services receive config models and return explicit results.
- External commands are wrapped in dedicated modules.
- Long-running work must not block the TUI thread.
- Every task should leave the product runnable.
- Every implementation task should update docs and create a report.
