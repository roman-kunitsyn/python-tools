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
- Sessions are currently created implicitly at startup from a timestamped
  folder under `logs/voice_notes`.
- SPACE start/stop recording flow.
- Per-recording duration limit defaults to 300 seconds and cannot exceed 300
  seconds.
- CLI and TUI show countdown while recording and auto-stop on overflow.
- Recorder adapter over the sibling `audio-record` package.
- Whisper transcriber wrapper that returns transcript text.
- Whisper runs in translate-to-English mode for all voice-note output.
- Whisper transcription now reports a clear runtime error when the output
  transcript file is missing after `whisper-cli` completes.
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

## Target TUI Requirements

The TUI should move from a single append-only transcript view to a session
workspace centered on a human-readable session folder:

- Show a startup modal when the TUI opens.
- Allow creating a new session with a default title that can be edited before
  start.
- Allow selecting an existing session from folders in `logs/voice_notes` and
  continuing that session.
- Rename session folders when the session title changes.
- Use a human-readable session folder shape such as
  `logs/voice_notes/{title-or-voice_note}-YYYY_MM_DD-HH_MM_SS`.
- Keep session artifacts human-readable and directly editable from disk.
- Show a session folder link after startup, not a transcript-file link.
- Show a QR code that opens the Telegram bot assistant for the active session.
- Make the recording state visibly different across the whole background.
- Add a blinking or otherwise attention-grabbing recording status bar.
- Add font-size controls for transcribed text with `+` and `-` buttons.
- Make the transcript view scrollable with newest items at the top.
- Let Enter open the session folder in the configured editor.
- Support configurable folder opening behavior for VS Code and `nvim`.
- Allow audio playback for a note when source audio exists.

## Storage Requirements

The session should use a hybrid artifact model:

- Session folder is the human-readable root for a single work session.
- Audio files remain in `audio/` and keep timestamped names.
- Transcript data should be stored in a rewriteable structured file, likely
  `notes.json`.
- `transcribe.txt` should remain present as a human-readable artifact, but it
  should be generated from `notes.json` after each update rather than treated as
  the primary source of truth.
- The transcript text file may stay named `transcribe.txt` or may be renamed to
  match the final data model, but the plan should preserve a direct-text file
  for reading and editing.
- Notes should support independent updates so individual entries can be edited,
  saved, canceled, removed, and augmented with manual typing.

## Planned Implementation Phases

1. Session model and discovery
- Add a session metadata model that captures folder name, title, timestamps,
  artifact paths, and display label.
- Add session discovery under `logs/voice_notes`.
- Add create/select/continue session flow for startup.
- Add rename support so changing the session title updates the folder name in a
  predictable human-readable way.

2. Storage and persistence
- Replace append-only transcript handling with a note collection backed by a
  structured session file.
- Keep `transcribe.txt` synchronized from the structured data.
- Preserve audio source paths for replay and later editing.
- Decide the final artifact name for the structured session file
  (`notes.json` preferred, `transcribe.json` acceptable if retained for
  compatibility).
- Make the structured file the source of truth for notes, edits, deletes, and
  manual text additions.

3. TUI layout and interaction
- Build the modal startup UI.
- Build the main workspace UI around a scrollable transcript pane, session
  summary, QR code, and session folder action.
- Add recording-state background changes and status animation.
- Add font size controls.
- Add note navigation, edit, save, cancel, delete, and manual add flows.
- Add note playback controls in the note detail area when source audio exists.

4. Editor and playback actions
- Make Enter open the session folder in the configured editor.
- Support configurable folder opening for VS Code and `nvim`.
- Add playback for notes that have source audio.

5. Documentation and tests
- Update README examples, screenshots, and keyboard shortcuts.
- Add tests for session creation, session resumption, folder renaming, note
  ordering, and editor/playback actions.
- Add report documentation after implementation.
- Write one report file per implementation task in `docs/reports/`, following
  the existing report naming convention.

## Task Breakdown

### Task 1: Session lifecycle
- Introduce session metadata and folder/title normalization rules.
- Implement session discovery, selection, and creation flow.
- Implement folder rename behavior when the session title changes.
- Add tests for session listing, selection, and rename behavior.
- Leave a report in `docs/reports/` describing the session lifecycle change.

### Task 2: Structured note storage
- Replace append-only transcript handling with a structured session note store.
- Generate `transcribe.txt` from the structured note file after each change.
- Keep audio file references in the structured data for playback and editing.
- Add tests for persistence, regeneration, and note ordering.
- Leave a report in `docs/reports/` describing the storage model change.

### Task 3: TUI workspace redesign
- Add the startup modal/screen for new or existing sessions.
- Add the session summary area, QR code block, and folder action.
- Add the recording visual treatment and status animation.
- Add font size controls and scrollable newest-first notes.
- Add tests for the new screen composition and bindings.
- Leave a report in `docs/reports/` describing the TUI redesign.

### Task 4: Note interactions
- Add independent per-note edit/save/cancel/delete actions.
- Add manual text note entry alongside voice notes.
- Add note playback when source audio exists.
- Add tests for note selection, editing, manual entry, and playback gating.
- Leave a report in `docs/reports/` describing the note interaction layer.

### Task 5: Editor and docs
- Make Enter open the session folder in the configured editor.
- Support configurable folder opening behavior for VS Code and `nvim`.
- Update README examples and keyboard shortcut documentation.
- Add final regression tests and update the top-level implementation plan.
- Leave a report in `docs/reports/` describing the final integration changes.

## Runtime Dependencies

- `ffmpeg` for recording through `audio-record`.
- `whisper-cli` for transcription.
- Whisper model files under `~/whisper/models`, or a direct model path passed
  with `--model`.
- `qrcode` for QR code generation in the TUI.
- An audio playback backend for note playback, if implemented in the same
  release.

## Remaining Enhancements

- Add packaging metadata if this workspace becomes an installed command suite.
- Add project script entries for future tools that need `uv run tool-name`.
- Add true global hotkeys only if a platform-specific dependency is accepted.
- Add integration tests with fake `ffmpeg` and `whisper-cli` executables.
