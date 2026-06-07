# Architecture Guideline

Use this guideline to build small production-grade Python tools that wrap one clear capability, such as audio transcription, meeting recording, note export, or file conversion.

The goal is a reusable app shape:

```text
external tool or domain function
service layer
shared config model
CLI and TUI presentation layers
thin script entry point
```

## Core Principle

Keep the project focused on one responsibility.

Good scope:

```text
audio file -> transcription file
```

Good scope:

```text
microphone input -> recorded audio file
```

Avoid mixing unrelated responsibilities in one tool. Meeting scheduling, recording, transcription, note generation, and task extraction should be separate tools or separate services with clear boundaries.

## Standard Structure

Use this structure for projects like this:

```text
tool-name/
├── tool-name.py
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDELINE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── reports/
└── src/
    ├── __init__.py
    └── app/
        ├── __init__.py
        ├── main.py
        ├── cli/
        │   ├── __init__.py
        │   └── parser.py
        ├── models/
        │   ├── __init__.py
        │   └── config.py
        ├── services/
        │   ├── __init__.py
        │   ├── domain_service.py
        │   └── external_tool.py
        └── ui/
            ├── __init__.py
            ├── app.py
            ├── forms/
            ├── screens/
            └── widgets/
```

For this project, `domain_service.py` is `transcriber.py` and `external_tool.py` is `whisper.py`.

## Entry Point

The root script should stay thin:

```python
from src.app.main import main


if __name__ == "__main__":
    raise SystemExit(main())
```

Do not put parsing, subprocess calls, validation, UI composition, or business logic in the script entry point.

## Shared Config Model

Every CLI/TUI tool should revolve around one config model.

Example:

```python
@dataclass
class TranscribeConfig:
    audio_file: Path | None
    output_file: Path | None
    output_format: str
    model_file: Path
    language: str = "auto"
```

The exact fields change per tool, but the rule stays the same:

```text
CLI fills config
TUI fills config
services consume config
```

Never pass `argparse.Namespace`, Textual widgets, raw form data, or UI state into the service layer.

## CLI Layer

The CLI layer owns argument definitions and conversion from arguments to config.

Responsibilities:

- expose stable command-line options
- parse paths as `Path`
- provide defaults
- build the shared config model
- keep CLI-only validation at the command boundary

The CLI layer should not:

- call subprocesses
- inspect output files
- own domain behavior
- know about Textual widgets or screens

## Service Layer

The service layer owns application behavior.

Responsibilities:

- validate domain inputs
- build output paths
- map user-facing options to external-tool flags
- orchestrate external wrappers
- return meaningful values such as output paths

Services should be importable and testable without launching the CLI or TUI.

## External Tool Wrapper

Wrap external processes in a dedicated module or class.

For a command-line tool wrapper:

- build commands as lists, not strings
- use `subprocess.run(command, check=True)`
- avoid shell invocation unless there is a specific, reviewed need
- let stdout/stderr stream unless the application needs to parse output
- keep external tool flags isolated in one place

This makes future replacements possible. For example, `whisper-cli` can be replaced by another transcription engine without rewriting the TUI.

## TUI Layer

Textual is a presentation layer.

Screens and widgets may:

- display values from config
- edit form values
- show progress and status
- call services at screen-level boundaries

Screens and widgets must not:

- build subprocess commands
- call external tools directly
- contain domain validation beyond immediate form validation
- duplicate service-layer path or format logic

Use screen-oriented flow:

```text
App
Screen
Form
Config
ProgressScreen
Service
ExternalToolWrapper
```

Use reusable widgets for repeated UI patterns:

- path inputs
- select fields
- action buttons
- footer bars
- file pickers
- confirmation dialogs

## Long-Running Work

Long-running work belongs behind a service boundary and should be launched from a screen that can display progress.

For Textual:

- use workers for blocking work
- update widgets from the app thread
- show a clear finished/error state
- provide a navigation action after completion

Do not block the main UI thread with external processes.

## Return Codes

Keep CLI return codes stable and documented.

Recommended baseline:

- `0`: success
- `1`: validation or user input error
- `2`: external tool failure
- `3`: configuration or environment error

Only add codes when they represent a real operational difference.

## Documentation Contract

Every project following this architecture should keep these documents current:

- `README.md`: how to run the app
- `docs/DEVELOPMENT_GUIDELINE.md`: project conventions
- `docs/ARCHITECTURE_GUIDELINE.md`: architecture rules
- `docs/IMPLEMENTATION_PLAN.md`: staged roadmap
- `docs/DEVELOPER_ROLE.md`: role summary
- `docs/python_tool_engineer.json`: machine-readable role profile

After each implementation task, add a report under `docs/reports/`.

## Agent Workflow

When an agent builds or extends a project like this, it should:

1. Read `docs/IMPLEMENTATION_PLAN.md`.
2. Inspect the current source tree.
3. Identify the layer affected by the task.
4. Implement one complete working slice.
5. Keep UI code separate from service and wrapper code.
6. Run relevant checks.
7. Update docs.
8. Write a short report in `docs/reports/`.
