# Implementation Guideline

This plan guides an agent from a draft script to a production-grade Python CLI/TUI tool. Each task should leave a working product, not a half-finished layer.

The agent should use:

- [Architecture Guideline](ARCHITECTURE_GUIDELINE.md)
- [Development Guideline](DEVELOPMENT_GUIDELINE.md)
- [Tool Engineer](./../roles/TOOL_ENGINEER.md)
- [python_tool_engineer.json](python_tool_engineer.json)

## Operating Rules

For every task:

1. Review the current project tree and relevant files.
2. Identify which architectural layers are affected.
3. Implement one complete functional slice.
4. Keep CLI, TUI, services, models, and external wrappers separate.
5. Run checks appropriate to the changed layer.
6. Update documentation.
7. Create a report in `docs/reports/`.

Report file format:

```text
docs/reports/report_{timestamp}.md
```

Use a sortable timestamp:

```text
report_2026-06-08_14-30-00.md
```

Each report should include:

- task summary
- files changed
- behavior added or changed
- checks run
- remaining risks or follow-up work

## Task 1: Convert Draft Script Into CLI Tool

Goal:

Create a working CLI that wraps one external tool or one focused capability.

Deliverables:

- thin root script
- argument parser
- validation functions
- output path builder
- external tool wrapper
- stable exit codes
- README usage examples

Acceptance criteria:

- `uv run python tool-name.py --help` works
- default command runs or fails with a clear validation error
- no hardcoded user-specific runtime paths except documented defaults
- root script contains no business logic

[For this project](./../../src/audio-transcribe/README.md), this task produced a CLI around `whisper-cli`.

## Task 2: Split Into Application Layers

Goal:

Separate parser, config model, service logic, external tool wrapper, and entry point.

Deliverables:

- `src/app/main.py`
- `src/app/cli/parser.py`
- `src/app/models/config.py`
- `src/app/services/domain_service.py`
- `src/app/services/external_tool.py`

Acceptance criteria:

- CLI builds a config model
- service receives the config model
- external wrapper owns subprocess execution
- service can be imported without launching CLI or TUI
- existing CLI behavior still works

For this project, the config model is `TranscribeConfig`, the service is `TranscribeService`, and the external wrapper is `WhisperWrapper`.

## Task 3: Add Textual TUI Layer

Goal:

Add a TUI that edits the same config model used by the CLI and calls the same service layer.

Deliverables:

- `src/app/ui/app.py`
- screen for the primary workflow
- form for editing config
- progress/result screen
- reusable widgets
- `--mode tui`

Acceptance criteria:

- `uv run python tool-name.py --mode tui` starts the TUI
- CLI args can pre-fill TUI fields
- TUI does not call external tools directly from widgets
- long-running work runs through a worker or equivalent non-blocking boundary
- completion state shows status and navigation

[For this project](./../../src/audio-transcribe/README.md), `TranscribeScreen` gathers transcription config and `ProgressScreen` runs transcription through `TranscribeService`.

## Task 4: Add Tests and Test Doubles

Goal:

Make core behavior verifiable without real external tools.

Deliverables:

- unit tests for config building
- unit tests for validation
- unit tests for output path generation
- service tests with a fake external wrapper
- TUI smoke tests with Textual `run_test()`

Acceptance criteria:

- tests do not require `whisper-cli`
- tests do not require real audio files except temporary fixtures
- external command construction is tested
- TUI screens mount and key form flows are verified

Recommended tools:

- `pytest`
- `tmp_path`
- fake wrapper classes
- Textual `run_test()`

## Task 5: Improve Runtime Feedback

Goal:

Make long-running operations understandable and recoverable.

Deliverables:

- clearer progress state
- finished state
- validation and external failure messages
- back/cancel navigation
- optional verbose output

Acceptance criteria:

- CLI returns documented exit codes
- TUI shows validation errors without crashing
- TUI shows external tool failure without closing unexpectedly
- loading indicator is hidden after completion
- user has a clear next action

## Task 6: Add Configuration and Environment Checks

Goal:

Make the tool easier to run repeatedly in different environments.

Deliverables:

- documented default config
- optional config file or environment variables where useful
- explicit external-tool availability check
- model/tool path validation

Acceptance criteria:

- missing external tool is reported clearly
- missing model/config paths are reported clearly
- defaults are documented
- config does not leak UI concerns into services

## Task 7: Package and Distribution Readiness

Goal:

Prepare the project for repeated local use or publication inside a larger tool workspace.

Deliverables:

- pyproject entry point, if appropriate
- dependency list
- README install/run section
- lint/test scripts
- release notes or changelog convention

Acceptance criteria:

- app can run from a clean checkout
- dependencies are explicit
- CLI entry point is stable
- docs explain how to verify the installation

## Task 8: Production Hardening

Goal:

Reduce operational surprises.

Deliverables:

- structured logging where needed
- graceful interruption handling
- safer output overwrite behavior
- optional dry-run command preview
- more complete error taxonomy
- docs for known limitations

Acceptance criteria:

- interrupted external process does not leave the app in an unclear state
- output overwrite behavior is explicit
- failure messages are actionable
- production usage docs are current

## Current Project Status

Implemented:

- thin entry point
- CLI mode
- shared `TranscribeConfig`
- service layer
- `whisper-cli` wrapper
- Textual TUI mode
- reusable TUI widgets
- progress/result screen
- architecture and development docs

Next recommended task:

Task 4, add tests and test doubles.

<!-- TODO -->

add more information about testing in file
tools/python/docs/guidelines/TESTING_GUIDELINE.md
