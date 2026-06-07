# Development Guideline

## Scope

Keep this project focused on one responsibility:

```text
audio file -> transcription file
```

Meeting metadata, timestamps, recording paths, and scheduling belong in caller tools such as a meeting recorder.

## CLI Shape

Expose CLI arguments through `src.app.cli.parser.build_parser()` and keep argument parsing inside `main()`.

Supported CLI options:

- `--mode`: `cli` or `tui`, default `cli`
- `--audio-file`: required source audio path
- `--format`: output format, default `txt`
- `--output-file`: optional output path or base name
- `--model-file`: Whisper model path
- `--language`: Whisper language, default `auto`
- `--verbose`: print command details

Avoid positional arguments for required inputs when the meaning is domain-specific. Prefer explicit flags.

In CLI mode, `--audio-file` is required. In TUI mode, the user may start without an audio file and fill it in the form.

CLI arguments should build a `TranscribeConfig` through `build_config_from_args()`. Do not pass raw `argparse` namespaces into services or UI code.

## TUI Shape

Textual is a presentation layer only.

Widgets and screens may read and edit a `TranscribeConfig`, but they must not call `whisper-cli`, inspect files directly beyond UI concerns, or own transcription behavior.

Use this flow:

```text
TranscribeApp
TranscribeScreen
TranscribeForm
TranscribeConfig
ProgressScreen
TranscribeService
WhisperWrapper
```

The TUI should support pre-filled values from CLI arguments:

```bash
uv run audio-transcribe.py \
  --mode tui \
  --audio-file meeting.wav \
  --format json
```

Reusable UI components belong under `src/app/ui/widgets/`. Screens belong under `src/app/ui/screens/`. Forms belong under `src/app/ui/forms/`.

The TUI model selector should list available model files from `DEFAULT_MODEL_DIR`, currently `~/whisper/models/`. Keep model discovery in a service/helper module, not inline inside widgets.

Keep future UI concepts screen-oriented:

- `TranscribeScreen`
- `ProgressScreen`
- `SettingsScreen`

Do not put long-running work directly in form or input widgets. Use a screen or service boundary so the UI can show progress and results.

## Function Boundaries

Keep `audio-transcribe.py` limited to importing and running the application entry point:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

Use this CLI call path:

```text
main()
build_config_from_args()
TranscribeService.transcribe()
WhisperWrapper.run()
```

Use this TUI call path:

```text
main()
build_config_from_args()
TranscribeApp.run()
TranscribeForm.build_config()
TranscribeService.transcribe()
WhisperWrapper.run()
```

Validation and path construction should stay in `src.app.services.transcriber`:

- `validate_audio_file()`
- `validate_model_file()`
- `build_output_file()`
- `get_whisper_flag()`

This keeps the CLI usable today and makes the code importable by another Python tool later.

## Config Model

Everything should revolve around `TranscribeConfig`:

```python
@dataclass
class TranscribeConfig:
    audio_file: Path | None
    output_file: Path | None
    output_format: str
    model_file: Path
    language: str = "auto"
```

The CLI fills this model from `argparse`. The TUI fills the same model from form fields. Services receive this model and do not depend on either interface.

## Formats

Add output formats by updating `FORMAT_TO_FLAG`.

Do not add repeated `if output_format == ...` branches for format handling. The mapping is the source of truth:

```python
FORMAT_TO_FLAG = {
    "txt": "-otxt",
    "json": "-oj",
    "srt": "-osrt",
}
```

`SUPPORTED_FORMATS` should derive from this mapping.

## Output Paths

Whisper appends the output extension itself, so pass the output path without a suffix to `whisper-cli`:

```python
str(output_file.with_suffix(""))
```

Apply the selected extension in `build_output_file()` so the rest of the application can reason about the final file path.

## Subprocesses

Call `subprocess.run(command, check=True)` for `whisper-cli` inside `WhisperWrapper`.

Do not capture subprocess output unless the application needs to parse or display it differently. Let `whisper-cli` stream output normally.

## Return Codes

Keep return codes stable:

- `0`: success
- `1`: validation error
- `2`: `whisper-cli` failed

`main()` should return these integers. The module entry point should raise `SystemExit(main())`.

## Style

- Use `Path` for filesystem paths.
- Keep constants at the top of the file.
- Keep validation errors clear and specific.
- Avoid hardcoded user-specific paths in implementation code.
- Keep UI code declarative and thin.
- Prefer small reusable Textual widgets over repeated raw inputs.

## Verification

Before handing off changes, run checks that match the touched layer:

- CLI/parser changes: run `uv run python audio-transcribe.py --help` and at least one validation-error command.
- Service changes: run focused unit tests when present, or exercise the service with a test double for `WhisperWrapper`.
- TUI changes: run a Textual mounted smoke test with `App.run_test()`.
- Syntax check: run `uv run python -m py_compile` for edited Python files.
- JSON docs: run `uv run python -m json.tool docs/python_tool_engineer.json`.

Do not leave generated `__pycache__` files in the working tree.

## Task Reports

After each completed implementation task, create a short report in:

```text
docs/reports/report_{timestamp}.md
```

Use a sortable timestamp such as:

```text
report_2026-06-08_14-30-00.md
```

Each report should include:

- task summary
- files changed
- behavior added or changed
- checks run
- remaining risks or follow-up work
