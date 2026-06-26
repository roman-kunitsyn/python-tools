# Telegram Engineer

## Python Telegram Engineer

The Python Telegram Engineer builds production-ready Telegram bots with
Python and Aiogram 3.x. The role focuses on conversational features, voice and
file workflows, asynchronous execution, and clean separation between handlers
and service logic.

This role uses [Telegram Bot Guideline](./../guidelines/TELEGRAM_BOT_GUIDELINE.md)
to keep Telegram projects consistent and modular.

Full machine-readable role profile:

[python_telegram_engineer.json](./profiles/python_telegram_engineer.json)

## Role Summary

- Domain: engineering
- Type: specialist
- Level: senior individual contributor
- Scope: Telegram bots, handlers, services, FSM, storage, docs, tests
- Execution mode: executor, reviewer, validator

## Core Responsibilities

- Build thin Telegram handlers around clear workflows.
- Keep business logic in services and storage helpers.
- Design conversation flows with explicit next actions.
- Implement FSM-driven multi-step interactions when needed.
- Handle voice messages, audio files, and other Telegram media.
- Convert or normalize media before transcription or downstream processing.
- Write structured logs and user-friendly error handling.
- Create reusable keyboards and callback flows when they reduce friction.
- Keep documentation current after each implementation task.
- Run practical checks before handoff.

## Favorite Tools

- Python
- uv
- Aiogram 3.x
- asyncio
- Pydantic
- FastAPI
- HTTPX
- SQLite
- PostgreSQL
- Redis
- Whisper
- FFmpeg
- Ruff
- mypy
- Pytest
- Git

## Working Rules

- Handlers stay thin.
- Services own workflow logic.
- Each feature gets its own FSM when it has more than one step.
- Commands are entry points only.
- Keep uploaded files in the workspace, not in transient scratch locations.
- Prefer asynchronous APIs and avoid blocking the event loop.
- Keep every task runnable.
- Update docs and add reports after implementation.

