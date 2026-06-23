# voice-note Implementation Plan

## Current State

Implemented:

- CLI entry point at `voice-note.py`.
- Project script entry point for `uv run voice-note`.
- Textual TUI mode with previous notes and status states.
- TUI status is displayed in the footer with state-specific background colors.
- TUI content header shows the session folder name and transcript file path.
- TUI transcript link and `o` binding open the transcript in the configured
  editor.
- SPACE start/stop recording flow.
- Per-recording duration limit defaults to 300 seconds and cannot exceed 300
  seconds.
- CLI and TUI show countdown while recording and auto-stop on overflow.
- Recorder adapter over the sibling `audio-record` package.
- Whisper transcriber wrapper that returns transcript text.
- Whisper runs in translate-to-English mode for all voice-note output.
- Stdout and append-to-file output writers.
- Structured JSON transcript output at `transcribe.json`.
- Default per-run storage under `logs/voice_notes/voice_note_{timestamp}` with
  audio in `audio/audio_{timestamp}.wav` and text in `transcribe.txt`.
- Each recording within a session writes a new timestamped audio file.
- Technical `ffmpeg` and `whisper-cli` output is routed to session `log.txt`.
- Default audio input is the built-in microphone; `--audio-device` can override
  the device name or id.
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
