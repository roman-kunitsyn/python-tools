# API Server

## Project Overview

`api-server` exposes the workspace tools through a small FastAPI HTTP API.
The server stays thin and delegates real work to service adapters that wrap the
existing tool behavior.

Supported tool areas:

- audio recording
- audio transcription
- meeting recording
- voice-note capture and transcription

## Requirements

- Python 3.14 or newer
- `uv`
- `fastapi`
- `uvicorn`
- `pydantic`
- `pydantic-settings`
- `httpx`

The workspace already declares these dependencies in the root project.

## Start

Show the server help:

```bash
uv run python src/api-server/api-server.py --help
```

Start the API server:

```bash
uv run python src/api-server/api-server.py
```

Use a different host or port:

```bash
uv run python src/api-server/api-server.py \
  --host 0.0.0.0 \
  --port 8000
```

Enable Uvicorn reload mode for local development:

```bash
uv run python src/api-server/api-server.py --reload
```

## API

### Health

Check server status and available tool areas:

```bash
GET /health
```

List tool metadata directly:

```bash
GET /tools
```

### Audio Recordings

Start a recording session:

```bash
POST /audio-recordings
```

Example body:

```json
{
  "device": "Built-in Microphone",
  "output_format": "wav",
  "sample_rate": 16000,
  "channels": 1
}
```

Stop a session:

```bash
POST /audio-recordings/{session_id}/stop
```

### Transcriptions

Transcribe an audio file with `whisper-cli`:

```bash
POST /transcriptions
```

Example body:

```json
{
  "audio_file": "meeting.wav",
  "output_format": "txt",
  "model_file": "/home/user/whisper/models/ggml-small.bin",
  "language": "auto"
}
```

### Meeting Recordings

Start a meeting recording session:

```bash
POST /meeting-recordings
```

Stop a session:

```bash
POST /meeting-recordings/{session_id}/stop
```

The server creates the meeting folder and metadata file when the session
starts.

### Voice Notes

Start a voice-note session:

```bash
POST /voice-notes
```

Stop a session, transcribe the recorded audio, and write transcript output:

```bash
POST /voice-notes/{session_id}/stop
```

## Project Structure

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

`api-server.py` is only the script entry point. Application behavior lives in
`src/app`.

## Documentation

- [Development Guideline](docs/DEVELOPMENT_GUIDELINE.md)
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [Reports](docs/reports/)

Shared workspace docs:

- [Architecture Guideline](../../docs/guidelines/ARCHITECTURE_GUIDELINE.md)
- [Implementation Guideline](../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md)
- [Tool Engineer](../../docs/roles/TOOL_ENGINEER.md)
