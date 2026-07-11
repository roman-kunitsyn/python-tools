# voice-note Implementation Plan

## Current State

Implemented:

- CLI entry point at `voice-note.py`.
- Project script entry point for `uv run voice-note`.
- CLI mode shows a session selector before recording starts so you can create a
  new session or open an existing one, then uses colorized timestamped status
  lines while recording and transcribing.
- CLI session header links to the full session folder name instead of the short
  session title.
- Existing CLI sessions are listed in newest-first order with the full folder
  name so the open action matches the on-disk session path.
- Each transcript entry uses a timestamped note header with a clickable
  full-session-folder link, a blank separator line, and then a plain text body
  that stays flush left without hanging indentation.
- CLI and TUI share the same recorder, transcriber, and output services.
- Textual TUI mode with Notes, Assistant, Session, Help, and Settings tabs.
- Notes are rendered oldest-to-newest, can be navigated with `j`/`k` and arrow
  keys, and support shift-range selection plus clipboard copy.
- Assistant messages use the same list-navigation, edit, delete, copy, and play
  controls as Notes.
- `p` toggles playback for the active note or assistant message, `s` stops
  playback, and starting a new playback stops the previous one.
- Text-only playback falls back to macOS `say` on supported systems.
- Assistant prompts can be recorded from voice or typed in an editor, then sent
  to Ollama as chat context over the current session notes.
- Assistant prompts and responses are stored in a human-readable session file
  alongside the note artifacts.
- Assistant prompt edits regenerate the paired response.
- TUI status is displayed in the footer with state-specific background colors.
- TUI transcript link and `o` binding open the transcript in the configured
  editor.
- Sessions are created from timestamped folders under `logs/voice_notes`.
- Per-recording duration limit defaults to 300 seconds and cannot exceed 300
  seconds.
- CLI and TUI show countdown while recording and auto-stop on overflow.
- Recorder adapter over the sibling `audio-record` package.
- Whisper transcriber wrapper that returns transcript text.
- Whisper runs in translate-to-English mode for all voice-note output.
- Whisper transcription reports a clear runtime error when the output
  transcript file is missing after `whisper-cli` completes.
- Stdout and append-to-file output writers.
- Structured note artifacts in `notes.json` and `transcribe.txt`, plus
  assistant artifacts in `assistant.json` and `assistant.txt`.
- Default per-run storage under `logs/voice_notes/voice_note_{timestamp}` with
  audio in `audio/audio_{timestamp}.wav` and text in `transcribe.txt`.
- Each recording within a session writes a new timestamped audio file.
- Technical `ffmpeg` and `whisper-cli` output is routed to session `log.txt`.
- Whisper transcription model and Ollama assistant model are now independent.
- Default audio input is the built-in microphone; `--audio-device` can override
  the device name or id.
- JSON config loading.
- Unit tests for service, TUI, playback, assistant storage, and config loading.

## Global Architecture Alignment

`voice-note` should stay aligned with the shared repository architecture while
keeping its module-specific details local.

Global docs should mention:

- `voice-note` as an example of a tool that has both CLI and TUI modes.
- the reusable tool shape: thin script entry point, shared config model,
  service layer, and presentation layers.
- Unix-style I/O expectations for CLI automation:
  - `--input` overrides `stdin`
  - `--output` overrides `stdout`
  - `--logs` or `--log-file` adds persistent logs but does not replace
    `stderr`
  - named CLI option values override `--config` values
- the report convention, including `commit_name`
- the role of `TOOL_ENGINEER` for implementation work

Local `voice-note` docs should keep:

- session storage layout and file names
- TUI navigation, bindings, and workspace behavior
- assistant/Ollama workflow details
- playback behavior, including macOS `say`
- note ordering, editing, selection, and clipboard rules
- module-specific runtime dependencies

Alignment plan:

1. Keep `README.md` focused on how to run `voice-note` and what modes it
   supports.
2. Keep `docs/IMPLEMENTATION_PLAN.md` focused on current behavior and feature
   slices.
3. Keep `docs/DEVELOPMENT_GUIDELINE.md` focused on module boundaries and
   implementation rules.
4. Use shared root docs for reusable conventions only.
5. Add or update module reports when behavior changes.
6. Split reusable code into CLI, services, and TUI components so local docs can
   refer to stable layers instead of one large app file.

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
- The TUI should gain a dedicated `Assistant` tab that behaves like a local
  Ollama chat surface over the current session notes.

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
- Assistant messages should support the same human-readable session storage
  pattern, plus prompt/response metadata needed for chat history, playback, and
  streaming state.
- The implementation should reuse shared widgets, models, and services instead
  of duplicating the Notes workflow.
- `voice_note/tui/app.py` should be split into smaller pieces before the
  Assistant workflow grows further.

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

### Task 6: Assistant message storage and prompt context

- Add a structured assistant message model with role, prompt text, response
  text, created_at, source audio, and generation state fields.
- Decide the assistant artifact layout, keeping it human-readable and editable
  on disk alongside the session folder.
- Add a context builder that turns the current session notes into Ollama-ready
  prompt context.
- Add tests for assistant message persistence and context assembly.
- Leave a report in `docs/reports/` describing the assistant storage and
  context slice.

### Task 7: Shared workspace components and app refactor

- Extract reusable TUI pieces for note cards, message cards, transcript/message
  lists, and detail panels so Notes and Assistant can share structure.
- Split `voice_note/tui/app.py` into a thinner app shell plus focused helper or
  widget modules.
- Keep the existing Notes behavior unchanged while moving shared rendering
  concerns out of the app body.
- Add tests that cover the extracted widgets and confirm the Notes tab still
  renders the same way.
- Leave a report in `docs/reports/` describing the shared-component refactor.
- Proposed module split:
  - `voice_note/tui/app.py`: app wiring, tab switching, status updates, note
    actions, assistant actions, and service orchestration.
  - `voice_note/tui/components.py`: reusable note/message card renderers and
    shared list helpers.
  - `voice_note/tui/layouts.py`: shared panel and workspace layout builders for
    Notes and Assistant tabs.
  - `voice_note/tui/views.py`: scrollable transcript/chat views and selection
    rendering logic.
  - `voice_note/tui/panels.py`: detail cards, session summary cards, and
    assistant response cards.
  - `voice_note/tui/assistant.py`: assistant-specific actions, prompt
    submission, and response state management.
- Refactor order:
  1. Extract shared card rendering used by Notes first.
  2. Extract the scrollable list/view helpers.
  3. Move Assistant-only logic into its own module.
  4. Trim `app.py` to tab orchestration and cross-cutting commands only.

### Task 8: Ollama client and response generation

- Add a local Ollama client/service that can send assistant prompts and current
  session context to the local server.
- Support non-streaming responses first, then preserve the API shape needed for
  later streaming support.
- Keep the client isolated from the TUI so it can be tested with fake HTTP
  responses.
- Add tests for request construction, response parsing, and error handling.
- Leave a report in `docs/reports/` describing the Ollama integration slice.

### Task 9: Assistant TUI chat workspace

- Turn the `Assistant` tab into a chat-like workspace that can record voice
  prompts, accept manual text prompts, and show Ollama responses inline.
- Render prompt and response cards with different visual treatment so the chat
  flow is easy to scan.
- Keep the same note-style navigation, edit, save, delete, and play controls for
  assistant messages, including replaying recorded prompt audio when available.
- Add optional streaming text updates so the response can appear as it is being
  generated.
- Add tests for assistant tab composition, prompt submission, response display,
  and playback behavior.
- Leave a report in `docs/reports/` describing the assistant chat workspace.

## Runtime Dependencies

- `ffmpeg` for recording through `audio-record`.
- `whisper-cli` for transcription.
- Whisper model files under `~/whisper/models`, or a direct model path passed
  with `--model`.
- `qrcode` for QR code generation in the TUI.
- An audio playback backend for note playback, if implemented in the same
  release.
- A local Ollama server for assistant responses, if the assistant tab is
  implemented in the same release.

## Remaining Enhancements

- Add packaging metadata if this workspace becomes an installed command suite.
- Add project script entries for future tools that need `uv run tool-name`.
- Add true global hotkeys only if a platform-specific dependency is accepted.
- Add integration tests with fake `ffmpeg` and `whisper-cli` executables.
