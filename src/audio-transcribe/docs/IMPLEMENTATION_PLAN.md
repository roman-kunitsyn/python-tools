# Audio Transcribe Implementation Plan

This document records the current implementation state of the `audio-transcribe`
module. Shared process guidance belongs in
[Implementation Guideline](../../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md).

## Module Purpose

`audio-transcribe` transcribes one audio file with `whisper-cli`.

Supported interfaces:

- CLI mode for direct transcription.
- Textual TUI mode for editing the same transcription config interactively.

The module should remain focused on this flow:

```text
audio file -> transcription file
```

Meeting-specific behavior, recording orchestration, and transcript post-
processing belong outside this module.

## Current Structure

```text
src/audio-transcribe/
├── audio-transcribe.py
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDELINE.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── reports/
│   └── tasks/
└── src/app/
    ├── cli/
    ├── models/
    ├── services/
    └── ui/
```

Current layer ownership:

- `audio-transcribe.py`: thin script entry point.
- `src/app/main.py`: mode dispatch, top-level CLI/TUI execution, and exit code
  mapping.
- `src/app/cli/parser.py`: argument parsing and config construction.
- `src/app/models/config.py`: `TranscribeConfig` and default model paths.
- `src/app/services/transcriber.py`: validation, output path building, format
  mapping, and transcription orchestration.
- `src/app/services/whisper.py`: `whisper-cli` subprocess command wrapper.
- `src/app/ui/`: Textual app, screens, form components, and widgets.

## Implemented

- Thin root script delegates into `src.app.main`.
- CLI mode accepts audio file, output format, output file base name, model file,
  language, verbose output, and mode selection.
- Shared `TranscribeConfig` is used by CLI and TUI paths.
- Service layer validates audio file, model file, and output format.
- Output file generation supports `txt`, `json`, and `srt`.
- `WhisperWrapper` owns `whisper-cli` subprocess execution.
- Textual TUI exists with transcription form, progress screen, reusable form
  widgets, and action/footer widgets.
- TUI mode can be started with CLI arguments used as initial config.
- README documents CLI usage, TUI usage, requirements, structure, and exit
  codes.
- Task reports exist for completed implementation work.

## Known Gaps

- Automated tests are not present yet.
- Core behavior still needs test doubles for `WhisperWrapper`.
- TUI smoke tests with Textual `run_test()` are not present.
- External tool availability is only discovered when the subprocess is invoked.
- Output overwrite behavior is not explicitly protected or documented.
- Runtime cancellation/interruption behavior is not documented.
- Packaging entry points and project-level install verification are not defined
  for this module.
- Error messages are functional, but the TUI needs broader validation and
  external failure coverage.

## Current Acceptance State

Completed:

- Part 1: Create a focused CLI wrapper around `whisper-cli`.
- Part 2: Split entry point, CLI parser, config model, service logic, and
  external tool wrapper.
- Part 3: Add a Textual TUI that edits the shared config and calls the service.

Partial:

- Part 5: Improve runtime feedback. CLI exit codes and basic TUI progress exist,
  but cancellation, recovery, and failure display need more coverage.
- Part 6: Add configuration and environment checks. Default model paths are
  documented, but explicit environment checks are not complete.

Not started:

- Part 4: Add tests and test doubles.
- Part 7: Package and distribution readiness.
- Part 8: Production hardening.

## Next Small Parts

### Part 4: Tests and Test Doubles

Goal:

Make core behavior verifiable without `whisper-cli` or real user audio files.

Deliverables:

- tests for argument parsing and config construction
- tests for output file generation
- tests for validation failures
- tests for `whisper-cli` command construction
- service tests using a fake wrapper
- basic TUI smoke tests with Textual `run_test()`

Acceptance criteria:

- tests do not require `whisper-cli`
- tests do not require real audio outside temporary fixtures
- subprocess command construction is covered
- TUI screens mount in a test harness

### Part 5: Runtime Feedback Completion

Goal:

Make long-running transcription status and failures clearer in CLI and TUI
modes.

Deliverables:

- clearer TUI validation messages
- external failure state in the TUI
- cancellation or back navigation behavior where appropriate
- documented verbose output behavior

Acceptance criteria:

- validation failures do not close the TUI unexpectedly
- external command failures produce an actionable message
- loading state is cleared after success or failure
- the user has an obvious next action after completion

### Part 6: Environment Checks

Goal:

Report missing runtime dependencies before starting work where possible.

Deliverables:

- explicit `whisper-cli` availability check
- clearer missing model file guidance
- optional model directory discovery behavior documented for the TUI

Acceptance criteria:

- missing `whisper-cli` is reported clearly
- missing model path is reported clearly
- service logic remains independent of UI concerns

### Part 7: Packaging Readiness

Goal:

Prepare the module for repeated local use from a clean checkout.

Deliverables:

- documented install and verification commands
- stable entry point decision
- dependency notes for Textual and external `whisper-cli`
- lint/test command documentation

Acceptance criteria:

- README explains how to verify installation
- dependencies are explicit
- CLI entry point remains stable

### Part 8: Production Hardening

Goal:

Reduce operational surprises during repeated transcription work.

Deliverables:

- explicit overwrite behavior
- optional dry-run command preview
- graceful interruption handling
- known limitations documentation

Acceptance criteria:

- interrupted transcription does not leave unclear app state
- overwrite behavior is predictable
- failure messages remain actionable

## Documentation Rules For This Module

When implementation changes:

1. Update this plan to reflect the real module state.
2. Update `README.md` if user-facing behavior changed.
3. Add a report under `docs/reports/`.
4. Keep proposed future work in `docs/tasks/` or the `Next Small Parts`
   section.

Do not copy shared implementation rules into this file unless they are being
made specific to `audio-transcribe`.
