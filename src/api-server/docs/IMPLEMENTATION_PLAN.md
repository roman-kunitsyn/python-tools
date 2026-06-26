# API Server Implementation Plan

## Module Purpose

`api-server` exposes the existing workspace tools through HTTP endpoints.

Current supported tool areas:

- audio recording
- audio transcription
- meeting recording
- voice-note capture and transcription

The API server should remain an adapter layer. The tool behavior belongs in the
services and existing workspace modules, not in the routers.

## Current Structure

```text
src/api-server/
├── api-server.py
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDELINE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── reports/
└── src/app/
    ├── bootstrap.py
    ├── config.py
    ├── dependencies.py
    ├── main.py
    ├── routers/
    ├── schemas/
    └── services/
```

Current layer ownership:

- `api-server.py`: thin entry point that bootstraps the app package and starts
  Uvicorn.
- `src/app/main.py`: FastAPI application factory and CLI server runner.
- `src/app/config.py`: server settings and default tool paths.
- `src/app/bootstrap.py`: workspace path bootstrap so the sibling tool
  packages can be imported.
- `src/app/services/`: tool-specific service adapters and session store.
- `src/app/routers/`: HTTP endpoints for health, audio recordings,
  transcriptions, meeting recordings, and voice notes.
- `src/app/schemas/`: request and response models.

## Implemented

- Thin script entry point for launching the API server.
- FastAPI app factory with shared tool catalog and health endpoint.
- HTTP routes for:
  - `GET /tools`
  - `POST /audio-recordings`
  - `POST /audio-recordings/{session_id}/stop`
  - `POST /transcriptions`
  - `POST /meeting-recordings`
  - `POST /meeting-recordings/{session_id}/stop`
  - `POST /voice-notes`
  - `POST /voice-notes/{session_id}/stop`
- Shared session store for long-running recording sessions.
- Tool adapters for ffmpeg recording, meeting recording metadata, whisper
  transcription, and voice-note capture/transcription.
- Module-local development guideline and README updates.
- Unit tests for health, service boundaries, and transcript wiring.

## Known Gaps

- No persistent session storage; active recordings live in memory only.
- No authentication or authorization.
- No upload-based transcription endpoint yet.
- No integration tests against real `ffmpeg` or `whisper-cli`.
- No OpenAPI examples or client SDKs yet.

## Current Acceptance State

Completed:

- Thin entry point and FastAPI app factory.
- Session-based HTTP API for the existing tools.
- Shared settings and route schemas.
- Initial unit tests.

Partial:

- Runtime feedback and error mapping could be refined with richer domain
  exceptions.
- Background persistence and restart recovery are not implemented.

Not started:

- Authentication.
- Persistent job/session storage.
- Production deployment packaging.

## Next Small Parts

### Part 2: Improve Error Mapping

Goal:

Map tool-specific failures to clearer HTTP responses.

Deliverables:

- dedicated exception types for missing tools and missing sessions
- friendlier 4xx/5xx responses from route handlers
- consistent error payload shapes

### Part 3: Add Integration Checks

Goal:

Verify the API against the real tool commands when the dependencies are
available.

Deliverables:

- smoke tests for `uv run python src/api-server/api-server.py --help`
- limited integration checks for the health and catalog endpoints
- optional environment-gated checks for `ffmpeg` and `whisper-cli`

### Part 4: Persistence and Deployment

Goal:

Prepare the API server for repeated use outside a single process lifetime.

Deliverables:

- persisted session/job storage
- deployment configuration
- startup readiness checks

## Documentation Rules For This Module

When implementation changes:

1. Update this plan to reflect the real module state.
2. Update `README.md` if user-facing behavior changed.
3. Add a report under `docs/reports/`.
4. Keep the routers thin and the service layer testable.
