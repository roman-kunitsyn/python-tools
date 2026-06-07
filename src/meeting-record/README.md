# Meeting Record

## Project Overview

Record a meeting audio session with `ffmpeg` on macOS using the `avfoundation`
input.

The tool finds an audio input device by name, creates a timestamped meeting
folder, records the core meeting audio file, and writes metadata for the
session.

## Goals

- Keep recording focused on one responsibility:
  `microphone input -> recorded audio file`.
- Keep the root script thin.
- Keep CLI parsing separate from recording behavior.
- Keep `ffmpeg` subprocess calls behind a wrapper.
- Store output in a predictable meeting folder.
- Preserve meeting metadata next to the recording.

## Tech Stack

- Python 3.14 or newer
- `uv`
- `argparse`
- `dataclasses`
- `pathlib`
- `subprocess`
- `ffmpeg`

## Getting Started

Show help:

```bash
uv run python src/meeting-record/meeting-record.py --help
```

Record with defaults:

```bash
uv run python src/meeting-record/meeting-record.py
```

By default, the tool looks for an audio input device containing:

```text
Aggregate Device
```

Default output root:

```text
~/workspace/meetings/
```

## CLI Usage

Record with a meeting stamp:

```bash
uv run python src/meeting-record/meeting-record.py \
  --stamp team-sync
```

Use a different input device name:

```bash
uv run python src/meeting-record/meeting-record.py \
  --device-name "MacBook Pro Microphone"
```

Use a different meetings directory:

```bash
uv run python src/meeting-record/meeting-record.py \
  --meetings-dir ~/recordings
```

Use a fixed timestamp for deterministic output paths:

```bash
uv run python src/meeting-record/meeting-record.py \
  --timestamp 2026_06_08-14_30_00
```

Print the `ffmpeg` record command:

```bash
uv run python src/meeting-record/meeting-record.py \
  --verbose
```

## Folder Structure

```text
meeting-record/
├── meeting-record.py
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDELINE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── reports/
└── src/app/
    ├── cli/
    ├── models/
    └── services/
```

## Examples

Default output:

```text
~/workspace/meetings/meeting-2026_06_08-14_30_00/
├── meeting-core-2026_06_08-14_30_00.wav
└── metadata.json
```

Metadata example:

```json
{
  "stamp": "team-sync",
  "timestamp": "2026_06_08-14_30_00"
}
```

## References

- [Root Architecture Guideline](../../docs/guidelines/ARCHITECTURE_GUIDELINE.md)
- [Root Implementation Guideline](../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md)
- [Tool Engineer Role](../../docs/roles/TOOL_ENGINEER.md)

## Documentation Links

- [Development Guideline](docs/DEVELOPMENT_GUIDELINE.md)
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [Reports](docs/reports/)
