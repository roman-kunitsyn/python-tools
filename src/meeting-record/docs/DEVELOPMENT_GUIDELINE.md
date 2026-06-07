# Meeting Record Development Guideline

Use this document for `meeting-record` specific conventions. Shared project
rules live in the root guidelines.

## Scope

This module records meeting audio. Keep it focused on:

```text
microphone input -> recorded audio file
```

Do not add splitting, transcription, summarization, calendar lookup, or note
generation to this module.

## Layer Rules

- `meeting-record.py` stays a thin entry point.
- `src/app/cli/parser.py` owns CLI arguments and `RecordConfig` construction.
- `src/app/models/config.py` owns config fields and defaults.
- `src/app/services/recorder.py` owns output paths, metadata, and orchestration.
- `src/app/services/ffmpeg.py` owns `ffmpeg` subprocess details.

## CLI Rules

- Prefer named options over unused positional arguments.
- Keep default output under `~/workspace/meetings`.
- Keep timestamp format compatible with existing meeting folders:
  `%Y_%m_%d-%H_%M_%S`.
- Use `--timestamp` only for deterministic paths or recovery workflows.

## Runtime Rules

- Build subprocess commands as lists.
- Do not use `shell=True`.
- Let `ffmpeg` stream normal recording output unless there is a specific reason
  to capture it.
- Treat existing meeting output directories as validation failures instead of
  overwriting them.

## Documentation Rules

After each implementation task:

1. Update `README.md` if user-facing behavior changed.
2. Update `docs/IMPLEMENTATION_PLAN.md` if module state changed.
3. Add a report in `docs/reports/`.
