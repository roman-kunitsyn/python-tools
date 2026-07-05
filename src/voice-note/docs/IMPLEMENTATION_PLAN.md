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

The TUI should evolve from a transcript viewer into a session workspace that is
fast to navigate from the keyboard:

- Notes should be readable oldest-to-newest, with the first note at the top.
- Note selection should work with `j`/`k` and the arrow keys.
- Tab switching should work with the arrow keys and `h`/`l`.
- Shift plus vertical navigation should extend a text-only selection across
  notes.
- Copying a selection should place plain text on the clipboard, without
  metadata.
- Pressing `p` on a note without source audio should speak the note with macOS
  built-in `say`.
- The TUI should gain a dedicated `Assistant` tab.

## Storage Requirements

The session should still use a human-readable session folder and a rewriteable
note store:

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

## Feature Plan

Each task below adds one user-visible feature and leaves the app runnable.
Tests and docs are part of the same slice so the behavior stays documented.

### Task 1: Oldest-first transcript ordering
- Change the transcript rendering and file regeneration so notes appear from
  oldest to newest.
- Keep the structured note store and `transcribe.txt` output in the same order.
- Add tests that verify the on-disk text and TUI render order.
- Leave a report in `docs/reports/` describing the ordering change.

### Task 2: Note navigation with arrows and vim keys
- Add note selection movement with `j`/`k` and the up/down arrow keys.
- Keep the focused note visible while navigating long transcripts.
- Add tests for key binding registration and selection movement.
- Leave a report in `docs/reports/` describing the navigation change.

### Task 3: Text selection and clipboard copy
- Add shift plus vertical navigation to extend a contiguous note selection.
- Copy selected note text to the clipboard as plain text only.
- Exclude timestamps, audio markers, and other metadata from copied output.
- Add tests for range selection formatting and clipboard adapter behavior.
- Leave a report in `docs/reports/` describing the copy workflow.

### Task 4: Tab navigation with `h` and `l`
- Add `h` and `l` bindings for moving between tabs.
- Keep left/right arrow tab switching intact.
- Add tests that verify all tab-switching bindings route to the same action.
- Leave a report in `docs/reports/` describing the tab-navigation change.

### Task 5: Playback for text-only notes
- Make `p` play note audio when a source file exists.
- Fall back to macOS built-in `say` for notes that have text but no audio.
- Keep the existing audio playback path for recorded notes.
- Add tests for playback selection and the text-to-speech fallback branch.
- Leave a report in `docs/reports/` describing the playback change.

### Task 6: Assistant tab
- Add a new `Assistant` tab to the TUI.
- Keep the tab integrated with the current keyboard navigation model.
- Add tests for tab presence, default focus, and tab switching.
- Leave a report in `docs/reports/` describing the new tab.

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
