# voice-note

`voice-note` is a terminal-first voice note tool with both CLI and Textual
TUI modes.

It supports:

- push-to-talk audio capture
- Whisper transcription
- rewriteable session note storage
- macOS text-to-speech fallback for text-only playback
- an Assistant tab that uses local Ollama with the current session notes as
  context

The TUI is the main workflow. Notes and Assistant share the same navigation,
selection, editing, playback, and clipboard patterns.

## Run

```bash
uv run voice-note
```

To start a specific mode:

```bash
uv run voice-note --mode cli
uv run voice-note --mode tui
```

If you want the script entry point directly:

```bash
uv run python src/voice-note/voice-note.py
```

## What It Stores

Each session creates a timestamped folder under `logs/voice_notes/`.

Typical session contents:

- `audio/` for retained recordings
- `transcribe.txt` for the human-readable transcript
- `notes.json` for structured note data
- `assistant.txt` and `assistant.json` for assistant history
- `log.txt` for technical tool output

## User Workflow

CLI mode is the lightweight terminal workflow for starting and stopping a
recording session. Before recording starts, it shows a session selector so you
can create a new session or open an existing one. If you create a new session,
it asks for a session name and shows the default in gray so you can press Enter
to accept it.

TUI mode is the main interactive workflow and provides:

- Notes, Assistant, Session, Help, and Settings tabs
- keyboard navigation for notes and tabs
- selection and clipboard copy
- note playback
- macOS `say` fallback for text-only playback
- session folder access from inside the app

The CLI also uses colorized timestamped status lines while recording and when
transcription starts, so the terminal output stays readable in longer sessions.
Each transcript entry is written as a timestamped note header with a clickable
full-session-folder link, then a blank separator line, then the plain text body
flush left without the extra hanging indentation.
The session header is a clickable link to the full session folder name, so you
can open the exact folder directly from the terminal output.

## Development Docs

The detailed architecture, feature slices, and work tracking live in module
docs:

- `docs/DEVELOPMENT_GUIDELINE.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/reports/`

Shared repository rules live in the root docs:

- `../../docs/guidelines/ARCHITECTURE_GUIDELINE.md`
- `../../docs/guidelines/PROJECT_DOCUMENTATION_GUIDELINE.md`
- `../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md`

## Notes

- `voice-note` is still in active development.
- The module is designed as a composition layer over reusable recorder,
  transcription, storage, and TUI components.
- Module-specific details should stay in the local docs so the README stays
  short and user-facing.
