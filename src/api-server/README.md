# API Server

## Project Overview

This module is a FastAPI-based HTTP adapter for the Python tools workspace.
Its job is to expose the existing tool capabilities through stable API
endpoints without moving business logic into the web layer.

The API server should stay thin and delegate real work to tool-specific
services or shared wrappers.

## Goals

- Keep the API layer focused on HTTP concerns only.
- Reuse the existing tool implementations instead of duplicating behavior.
- Keep request and response validation in Pydantic models.
- Keep subprocess calls and external tool usage in service or wrapper modules.
- Match the documentation pattern used by the other tool modules in this repo.

## Current Workspace Context

The repository already contains focused tool modules for:

- [audio-transcribe](../audio-transcribe/README.md)
- [meeting-record](../meeting-record/README.md)
- [audio-record](../audio-record/README.md)
- [voice-note](../voice-note/README.md)

Those tools already define the domain behavior that an API layer can wrap.
The server should not reimplement transcription, recording, or note handling.

## Recommended API Surface

Start with a small set of endpoints that map to the current tools:

- `GET /health`
- `POST /audio-recordings`
- `POST /transcriptions`
- `POST /meeting-recordings`
- `POST /voice-notes`

Keep each route narrow. A router should translate HTTP input into a config
model, call a service, and return a response model.

## Suggested Project Structure

The API server should follow the same module shape used by the other tools in
this repo:

```text
src/api-server/
├── api-server.py
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDELINE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── reports/
└── src/app/
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── dependencies.py
    ├── routers/
    ├── schemas/
    ├── services/
    ├── middleware/
    └── exceptions/
```

`api-server.py` should remain a thin entry point. All application behavior
should live under `src/app`.

## Layer Responsibilities

### Routers

- Define HTTP routes and status codes.
- Parse request payloads into schema objects.
- Call services.
- Return response models.

Routers should not contain business logic or subprocess calls.

### Schemas

- Define request and response models with Pydantic.
- Keep the HTTP contract explicit and stable.
- Convert tool outputs into API-friendly shapes.

### Services

- Orchestrate work for one feature area.
- Map API inputs to the existing tool configurations.
- Call lower-level wrappers or module services.
- Return explicit results such as file paths, text, or metadata.

### Config

- Load environment settings and shared defaults.
- Keep API-wide settings in one place.
- Avoid hardcoding paths or secrets in routers.

### Dependencies

- Provide reusable FastAPI dependency factories.
- Keep wiring code out of route handlers.

## Tech Stack

- Python 3.14 or newer
- `uv`
- `FastAPI`
- `uvicorn`
- `pydantic`
- `pydantic-settings`
- `httpx`

Optional later additions:

- `orjson` for faster JSON responses
- `python-multipart` if file uploads are part of the API

## Suggested Runtime Flow

```text
HTTP request
  -> router
  -> request schema
  -> service
  -> tool adapter or shared module
  -> response schema
  -> JSON response
```

The router should never call the external command directly.

## Development Notes

- Keep the server small and composable.
- Prefer one router per tool domain.
- Reuse the existing tool module behavior instead of duplicating it here.
- Add `docs/IMPLEMENTATION_PLAN.md` and `docs/reports/` once implementation
  begins.

## References

- [Architecture Guideline](../../docs/guidelines/ARCHITECTURE_GUIDELINE.md)
- [Implementation Guideline](../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md)
- [Tool Engineer](../../docs/roles/TOOL_ENGINEER.md)

