For your stack, I would keep the FastAPI layer **very small**. It should be an HTTP adapter, not where your business logic lives.

## Core stack

```toml
fastapi
uvicorn[standard]
pydantic
pydantic-settings
httpx
```

These are enough to build a production API.

---

## Project structure

```text
apps/
    api/
        main.py
        config.py

        routers/
            voice.py
            meeting.py
            notes.py

        dependencies.py

        middleware/

        exceptions/

        schemas/

        startup.py

packages/
    voice/
    meeting/
    transcription/
    audio/
```

Notice that `routers` should only call services from `packages`.

---

## I would use these libraries

### Framework

- **FastAPI** – API framework
- **Uvicorn** – ASGI server

```bash
uv add fastapi uvicorn
```

---

### Configuration

```bash
uv add pydantic-settings
```

```python
class Settings(BaseSettings):
    supabase_url: str
    telegram_token: str
```

---

### HTTP Client

```bash
uv add httpx
```

Useful for:

- Telegram API
- OpenAI
- Ollama
- n8n
- other REST APIs

---

### Validation

Already included.

```python
from pydantic import BaseModel
```

Example:

```python
class VoiceResponse(BaseModel):
    text: str
    language: str
```

---

### Background Tasks

Initially, use FastAPI's built-in support.

```python
from fastapi import BackgroundTasks
```

Later, if you need distributed jobs:

- Dramatiq
- Celery
- Arq

For your current project, I wouldn't add any of them yet.

---

### Logging

```bash
uv add structlog
```

or simply use

```python
import logging
```

You already have a logging system, so the standard library may be enough.

---

### Authentication

Since you're already using Supabase:

- JWT validation
- Supabase Auth

No need to build your own authentication.

---

## What I would NOT install initially

I would avoid adding these until you actually need them:

- SQLAlchemy
- Alembic
- Celery
- Redis
- ORM frameworks

Supabase already gives you PostgreSQL, authentication, and migrations. If you're accessing the database through Supabase (or its REST/RPC interface), you can keep the API layer much simpler.

---

## Typical request flow

```text
Request

    │

Router

    │

Pydantic Request Model

    │

VoiceService

    │

Packages

    │

Pydantic Response Model

    │

JSON
```

Notice that the router **never** contains business logic.

---

## Dependency Injection

FastAPI's built-in dependency system is enough.

```python
@router.post("/transcribe")
async def transcribe(
    service: VoiceService = Depends(get_voice_service),
):
    ...
```

I would **not** introduce a DI container unless the project becomes significantly larger.

---

## My recommended `pyproject.toml`

```toml
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "pydantic",
    "pydantic-settings",
    "httpx",
    "python-multipart",
    "orjson",
]
```

### Why these two extra packages?

- **python-multipart**: required for file uploads (`UploadFile`), which you'll need for audio files.
- **orjson**: a very fast JSON serializer that FastAPI can use for responses.

---

### As your platform grows

I can imagine your FastAPI layer remaining surprisingly small:

```text
apps/api/

~15-20 routers
~10 request/response models
~5 middleware components

Everything else lives in reusable packages.
```

That's a good sign—it means FastAPI is doing its job as an interface layer, while the real application logic stays reusable across your CLI, Telegram bot, Textual apps, and web frontend.

I see it like

POST api/voice-note/list
request {}
responce {}

POST api/voice-note/create
request {}
responce {}

POST api/voice-note/delete
request {}
responce {}

POST api/time-manager/start
request {}
responce {}

POST api/time-manager/stop
request {}
responce {}
