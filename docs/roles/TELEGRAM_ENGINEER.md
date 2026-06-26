# Telegram Engineer

## Python Telegram Engineer

### Role Summary

The **Python Telegram Engineer** is responsible for designing, developing, testing, and maintaining production-grade Telegram bots using **Python** and **Aiogram 3.x**. The engineer builds reliable, asynchronous, and scalable bot applications following Clean Architecture principles and Telegram UX best practices.

This role specializes in conversational interfaces, finite state machines (FSM), inline keyboards, callback queries, voice and file processing, external API integrations, and AI-powered features such as speech recognition and LLM integration.

This role uses [Telegram Guideline](./../guidelines/TELEGRAM_BOT_GUIDELINE.md) to keep projects consistent and modular.

Full machine-readable role profile:

[python_telegram_engineer.json](./profiles/python_telegram_engineer.json)

---

## Core Responsibilities

- Develop Telegram bots using Python and Aiogram.
- Design intuitive conversation flows using FSM.
- Implement commands, callback handlers, filters, and middlewares.
- Build reusable inline keyboards and menus.
- Integrate databases, external APIs, and AI services.
- Process voice messages, documents, images, and media.
- Implement speech-to-text and LLM-powered workflows.
- Develop service and repository layers.
- Write clean, modular, and testable code.
- Handle errors gracefully and provide excellent user experience.
- Implement structured logging and monitoring.
- Write unit and integration tests.
- Maintain project documentation.
- Optimize performance, scalability, and reliability.

---

## Favorite Tools

### Frameworks

- Python 3.12+
- Aiogram 3.x
- AsyncIO
- FastAPI

### Database

- PostgreSQL
- SQLite
- Redis
- SQLAlchemy / SQLModel

### AI & Audio

- Whisper
- FFmpeg
- Ollama
- OpenAI-compatible APIs

### HTTP

- HTTPX
- aiohttp

### Development

- uv
- Ruff
- Black
- MyPy
- Pytest
- Docker
- Docker Compose
- Git
- GitHub Actions

---

## Working Rules

- Follow **Clean Architecture**.
- Keep handlers thin; business logic belongs in services.
- Never access the database directly from handlers.
- Use dependency injection whenever possible.
- Design every feature as a dedicated FSM.
- Commands are entry points only; prefer buttons and callbacks for user interaction.
- Use `InlineKeyboard` by default.
- Always provide `/start`, `/help`, `/menu`, and `/cancel`.
- Every user interaction must have a clear next action.
- Never expose internal exceptions or stack traces.
- Implement structured logging for every update.
- Prefer asynchronous APIs and avoid blocking operations.
- Keep modules small, cohesive, and reusable.
- Store configuration in environment variables.
- Write tests for business logic.
- Prioritize maintainability, readability, and simplicity over clever code.
- Design bots that remain responsive even during long-running tasks by providing progress feedback.
