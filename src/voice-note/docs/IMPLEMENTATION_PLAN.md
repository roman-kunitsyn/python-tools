# voice-note Implementation Plan

## Current State

Implemented:

- CLI entry point at `voice-note.py`.
- Project script entry point for `uv run voice-note`.
- Textual TUI mode with previous notes and status states.
- SPACE start/stop recording flow.
- Recorder adapter over the sibling `audio-record` package.
- Whisper transcriber wrapper that returns transcript text.
- Stdout and append-to-file output writers.
- Optional timestamps.
- JSON config loading.
- Unit tests for service, timestamp formatting, config loading, and file output.

## Runtime Dependencies

- `ffmpeg` for recording through `audio-record`.
- `whisper-cli` for transcription.
- Whisper model files under `~/whisper/models`, or a direct model path passed
  with `--model`.

## Remaining Enhancements

- Add packaging metadata if this workspace becomes an installed command suite.
- Add project script entries for future tools that need `uv run tool-name`.
- Add true global hotkeys only if a platform-specific dependency is accepted.
- Add richer TUI controls for model, language, and output file selection.
- Add integration tests with fake `ffmpeg` and `whisper-cli` executables.
