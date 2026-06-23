# voice-note Development Guideline

## Responsibility

`voice-note` coordinates push-to-talk audio capture, speech-to-text
transcription, and note output.

It should compose lower-level tools instead of replacing them:

- `audio-record` owns microphone recording.
- `whisper-cli` / `audio-transcribe` conventions own transcription.
- `voice-note` owns workflow orchestration and note persistence.

## Architecture

- `voice-note.py` is a thin script entry point.
- `voice_note.cli` owns CLI arguments and terminal key handling.
- `voice_note.tui` owns Textual widgets and key bindings.
- `voice_note.audio` adapts the `audio-record` API.
- `voice_note.transcription` wraps Whisper transcription into `Path -> str`.
- `voice_note.output` owns stdout/file writing.
- `voice_note.services` coordinates the workflow.

## Rules

- Do not put subprocess commands in UI code.
- Do not put file persistence rules in UI code.
- Keep recorder, transcriber, writer, and controller testable with fakes.
- Do not add summarization, formatting, LLM processing, or note management here.

## Terminal Behavior

Portable terminal input exposes key presses, not reliable key release events.
The CLI therefore uses SPACE as a start/stop toggle. The TUI uses the same
SPACE toggle so the behavior is consistent.
