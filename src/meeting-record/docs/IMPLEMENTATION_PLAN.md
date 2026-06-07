# Meeting Record Implementation Plan

This document records the current implementation state of the `meeting-record`
module. Shared process guidance belongs in
[Implementation Guideline](../../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md).

## Module Purpose

`meeting-record` records one meeting audio session with `ffmpeg`.

Supported interface:

- CLI mode for starting a recording.

The module should remain focused on this flow:

```text
microphone input -> recorded audio file
```

Meeting splitting, transcription, summarization, scheduling, and post-processing
belong outside this module.

## Current Structure

```text
src/meeting-record/
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

Current layer ownership:

- `meeting-record.py`: thin script entry point.
- `src/app/main.py`: top-level CLI execution and exit code mapping.
- `src/app/cli/parser.py`: argument parsing and config construction.
- `src/app/models/config.py`: `RecordConfig` and defaults.
- `src/app/services/recorder.py`: timestamp handling, output path building,
  metadata writing, and recording orchestration.
- `src/app/services/ffmpeg.py`: `ffmpeg` device discovery and recording
  subprocess wrapper.
- `src/app/services/models.py`: service result model.

## Implemented

- Thin root entry point delegates into `src.app.main`.
- CLI mode accepts meeting stamp, meetings directory, device name, timestamp,
  and verbose output.
- Shared `RecordConfig` carries CLI settings into the service layer.
- Service layer builds timestamped meeting directories and output file paths.
- Metadata is written to `metadata.json`.
- `FfmpegWrapper` owns `ffmpeg` subprocess calls.
- CLI return codes are mapped for validation errors, existing output folders,
  external `ffmpeg` failures, and interruption.
- README documents setup, CLI usage, output structure, and references.

## Known Gaps

- Automated tests are not present yet.
- Core behavior needs test doubles for `FfmpegWrapper`.
- `ffmpeg` availability is only discovered when a subprocess is invoked.
- Device discovery is macOS `avfoundation` specific.
- There is no TUI mode.
- Interruption behavior is basic and should be tested with real `ffmpeg`
  recording.
- Output overwrite behavior is currently conservative because existing meeting
  directories fail with `FileExistsError`.

## Current Acceptance State

Completed:

- Part 1: Convert draft script into a focused CLI tool.
- Part 2: Split entry point, CLI parser, config model, service logic, and
  external tool wrapper.

Partial:

- Part 5: Improve runtime feedback. CLI return codes and verbose command output
  exist, but recovery guidance can be improved.
- Part 6: Add configuration and environment checks. Device name and meetings
  directory are configurable, but explicit `ffmpeg` availability checks are not
  complete.

Not started:

- Part 3: Add Textual TUI layer.
- Part 4: Add tests and test doubles.
- Part 7: Package and distribution readiness.
- Part 8: Production hardening.

## Next Small Parts

### Part 4: Tests and Test Doubles

Goal:

Make core behavior verifiable without invoking real `ffmpeg`.

Deliverables:

- tests for argument parsing and config construction
- tests for timestamp validation
- tests for meeting directory and audio file path generation
- service tests using a fake `ffmpeg` wrapper
- wrapper tests for device-code parsing from sample `ffmpeg` output

Acceptance criteria:

- tests do not require `ffmpeg`
- tests do not record real audio
- metadata payload is covered
- existing output directory behavior is covered

### Part 6: Environment Checks

Goal:

Report missing runtime dependencies before starting a recording where possible.

Deliverables:

- explicit `ffmpeg` availability check
- clearer device-not-found guidance
- optional command for listing available devices

Acceptance criteria:

- missing `ffmpeg` is reported clearly
- missing device name is reported clearly
- service logic remains independent of CLI formatting concerns

### Part 3: TUI Layer

Goal:

Add a Textual UI for configuring and starting a recording.

Deliverables:

- screen for recording config
- fields for stamp, meetings directory, and device name
- progress screen for active recording
- non-blocking worker boundary for `ffmpeg`

Acceptance criteria:

- TUI does not call `ffmpeg` directly from widgets
- TUI builds the same `RecordConfig` used by CLI mode
- active recording does not block the UI thread

### Part 8: Production Hardening

Goal:

Reduce operational surprises during repeated meeting recording.

Deliverables:

- graceful interruption handling verified against real `ffmpeg`
- clearer metadata write timing
- optional dry-run preview
- known limitations documentation

Acceptance criteria:

- interrupted recording leaves an understandable state
- output directory behavior is documented
- failure messages remain actionable

## Documentation Rules For This Module

When implementation changes:

1. Update this plan to reflect the real module state.
2. Update `README.md` if user-facing behavior changed.
3. Add a report under `docs/reports/`.
4. Keep proposed future work in `docs/tasks/` or the `Next Small Parts`
   section.
