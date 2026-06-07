# Development Guideline

## Scope

Keep this project focused on one responsibility:

```text
audio file -> transcription file
```

Meeting metadata, timestamps, recording paths, and scheduling belong in caller tools such as a meeting recorder.

## CLI Shape

Expose CLI arguments through `build_parser()` and keep argument parsing inside `main()`.

Supported CLI options:

- `--audio-file`: required source audio path
- `--format`: output format, default `txt`
- `--output-file`: optional output path or base name
- `--model-file`: Whisper model path
- `--language`: Whisper language, default `auto`
- `--verbose`: print command details

Avoid positional arguments for required inputs when the meaning is domain-specific. Prefer explicit flags.

## Function Boundaries

Keep module-level code limited to constants, function definitions, and:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

Use this call path:

```text
main()
transcribe_audio()
run_whisper()
```

Validation and path construction should stay in small functions:

- `validate_audio_file()`
- `validate_model_file()`
- `build_output_file()`
- `get_whisper_flag()`

This keeps the CLI usable today and makes the code importable by another Python tool later.

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

Call `subprocess.run(command, check=True)` for `whisper-cli`.

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
- Use `log(message, verbose)` for optional CLI logging.
- Avoid hardcoded user-specific paths in implementation code.
