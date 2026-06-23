# Python Tools

## Project Overview

This repository is a workspace for small Python tools. Each production-ready
tool should wrap one focused capability, expose a clear CLI or TUI, and keep
implementation state documented in its own module docs.

The current modular tools are:

- [audio-transcribe](src/audio-transcribe/README.md): transcribes audio files
  with `whisper-cli`.
- [meeting-record](src/meeting-record/README.md): records meeting audio with
  `ffmpeg`.
- [audio-record](src/audio-record/README.md): records raw audio files with
  `ffmpeg` for reuse by higher-level tools.
- [voice-note](src/voice-note/README.md): captures push-to-talk voice notes,
  transcribes them, and writes text to stdout or a notes file.

The remaining root `src/meeting-*.py` files are draft scripts. They are useful
source material for future tools, but they do not yet follow the full modular
CLI/TUI/service structure.

## Goals

- Keep each tool focused on one responsibility.
- Use thin script entry points.
- Keep CLI and TUI code as presentation layers.
- Pass structured config models into service layers.
- Wrap external tools behind dedicated modules.
- Keep shared guidelines separate from module-specific implementation state.
- Keep documentation synchronized after every implementation task.

## Tech Stack

- Python 3.14 or newer
- `uv` for dependency and command execution
- `argparse` for CLI interfaces
- `dataclasses` and `pathlib` for config and paths
- `subprocess` for external tool wrappers
- Textual and Rich for TUI and terminal UI work

Project dependencies are declared in [pyproject.toml](pyproject.toml).

## Getting Started

Install dependencies:

```bash
uv sync
```

Verify the current modular tool starts:

```bash
uv run python src/audio-transcribe/audio-transcribe.py --help
uv run python src/meeting-record/meeting-record.py --help
uv run python src/audio-record/audio-record.py --help
uv run python src/voice-note/voice-note.py --help
uv run voice-note --help
```

For audio transcription runtime requirements, see the
[audio-transcribe README](src/audio-transcribe/README.md). That tool requires
`whisper-cli` and a Whisper model file.

For meeting recording runtime requirements, see the
[meeting-record README](src/meeting-record/README.md). That tool requires
`ffmpeg` and a macOS audio input device visible to `avfoundation`.

For reusable raw audio recording, see the
[audio-record README](src/audio-record/README.md). That tool requires `ffmpeg`.

For push-to-talk voice notes, see the
[voice-note README](src/voice-note/README.md). That tool requires `ffmpeg`,
`whisper-cli`, and a Whisper model file.

## CLI Usage

Show help for the current modular tool:

```bash
uv run python src/audio-transcribe/audio-transcribe.py --help
uv run python src/meeting-record/meeting-record.py --help
uv run python src/audio-record/audio-record.py --help
uv run python src/voice-note/voice-note.py --help
uv run voice-note --help
```

Run audio transcription:

```bash
uv run python src/audio-transcribe/audio-transcribe.py \
  --audio-file meeting.wav
```

Start the Textual TUI:

```bash
uv run python src/audio-transcribe/audio-transcribe.py \
  --mode tui
```

Record a meeting:

```bash
uv run python src/meeting-record/meeting-record.py \
  --stamp team-sync
```

Record a raw audio file:

```bash
uv run python src/audio-record/audio-record.py output.wav --duration 30
```

Capture voice notes:

```bash
uv run python src/voice-note/voice-note.py --text-output-file notes.md
```

By default, voice-note stores a run under:

```text
logs/voice_notes/voice_note_{YYYY_MM_DD-HH_MM_SS}/
├── audio/audio_{recording_timestamp}.wav
├── log.txt
└── transcribe.txt
```

After `uv sync`, the installed project script can also be used:

```bash
uv run voice-note --text-output-file notes.md
```

Older draft scripts live directly under `src/`:

```text
src/meeting-split.py
src/meeting-transcribe.py
src/meeting-combine.py
src/meeting-summary.py
```

Treat them as drafts until they are moved into module directories with local
docs and the standard application structure.

## Folder Structure

```text
tools/python/
├── README.md
├── pyproject.toml
├── docs/
│   ├── guidelines/
│   └── roles/
└── src/
    ├── audio-transcribe/
    │   ├── README.md
    │   ├── audio-transcribe.py
    │   ├── docs/
    │   └── src/app/
    ├── meeting-record/
    │   ├── README.md
    │   ├── meeting-record.py
    │   ├── docs/
    │   └── src/app/
    ├── audio-record/
    │   ├── README.md
    │   ├── audio-record.py
    │   ├── audio_record/
    │   └── docs/
    ├── voice-note/
    │   ├── README.md
    │   ├── voice-note.py
    │   ├── voice_note/
    │   ├── tests/
    │   └── docs/
    ├── meeting-combine.py
    ├── meeting-split.py
    ├── meeting-summary.py
    └── meeting-transcribe.py
```

Standard production tool shape:

```text
src/tool-name/
├── tool-name.py
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDELINE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── reports/
└── src/app/
```

## Examples

Create a text transcript next to an audio file:

```bash
uv run python src/audio-transcribe/audio-transcribe.py \
  --audio-file meeting.wav
```

Create JSON output:

```bash
uv run python src/audio-transcribe/audio-transcribe.py \
  --audio-file meeting.wav \
  --format json
```

Use a custom model:

```bash
uv run python src/audio-transcribe/audio-transcribe.py \
  --audio-file meeting.wav \
  --model-file ~/whisper/models/ggml-medium.bin
```

Record a meeting to `~/workspace/meetings`:

```bash
uv run python src/meeting-record/meeting-record.py \
  --stamp team-sync
```

## References

Shared guidelines:

- [Architecture Guideline](docs/guidelines/ARCHITECTURE_GUIDELINE.md)
- [Implementation Guideline](docs/guidelines/IMPLEMENTATION_GUIDELINE.md)
- [Project Documentation Guideline](docs/guidelines/PROJECT_DOCUMENTATION_GUIDELINE.md)
- [Testing Guideline](docs/guidelines/TESTING_GUIDELINE.md)
- [UX/UI Design Guideline](docs/guidelines/UX_UI_DESIGN_GUIDELINE.md)
- [Investigation, Review, Planning, Prototyping](docs/guidelines/INVESTIGATION_REVIEW_PLANNING_PROTOTYPING.md)

Roles:

- [Product Owner](docs/roles/PRODUCT_OWNER.md)
- [Technical Lead](docs/roles/TECHNICAL_LEAD.md)
- [Tool Engineer](docs/roles/TOOL_ENGINEER.md)
- [Testing Engineer](docs/roles/TESTING_ENGINEER.md)
- [UI/UX Designer](docs/roles/UI_UX_DESIGNER.md)
- [Role Profiles](docs/roles/profiles)

## Documentation Links

Module documentation:

- [audio-transcribe README](src/audio-transcribe/README.md)
- [audio-transcribe Implementation Plan](src/audio-transcribe/docs/IMPLEMENTATION_PLAN.md)
- [audio-transcribe Development Guideline](src/audio-transcribe/docs/DEVELOPMENT_GUIDELINE.md)
- [audio-transcribe Task Reports](src/audio-transcribe/docs/reports/)
- [audio-transcribe Tasks](src/audio-transcribe/docs/tasks/)
- [meeting-record README](src/meeting-record/README.md)
- [meeting-record Implementation Plan](src/meeting-record/docs/IMPLEMENTATION_PLAN.md)
- [meeting-record Development Guideline](src/meeting-record/docs/DEVELOPMENT_GUIDELINE.md)
- [meeting-record Task Reports](src/meeting-record/docs/reports/)
- [audio-record README](src/audio-record/README.md)
- [audio-record Implementation Plan](src/audio-record/docs/IMPLEMENTATION_PLAN.md)
- [audio-record Development Guideline](src/audio-record/docs/DEVELOPMENT_GUIDELINE.md)
- [audio-record Task Reports](src/audio-record/docs/reports/)
- [voice-note README](src/voice-note/README.md)
- [voice-note Implementation Plan](src/voice-note/docs/IMPLEMENTATION_PLAN.md)
- [voice-note Development Guideline](src/voice-note/docs/DEVELOPMENT_GUIDELINE.md)
- [voice-note Task Reports](src/voice-note/docs/reports/)

Documentation responsibilities:

- Root `README.md`: workspace overview, setup, examples, and navigation.
- Shared `docs/guidelines/`: reusable rules for all tools.
- Shared `docs/roles/`: role responsibilities and review lenses.
- Module `README.md`: how to install, run, and use one tool.
- Module `docs/IMPLEMENTATION_PLAN.md`: current state, gaps, and next small
  parts for one tool.
- Module `docs/tasks/`: proposed or planned work.
- Module `docs/reports/`: completed work, checks run, and remaining risks.

When code changes, update the affected module docs, add a report under
`docs/reports/`, and update this README only when workspace navigation or setup
changes.
