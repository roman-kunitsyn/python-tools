# Task: Implement `voice-note` CLI/TUI Tool

## Objective

Implement a reusable Python utility named `voice-note` that provides push-to-talk voice capture, speech-to-text transcription, and optional note persistence.

The tool should work as both:

- CLI application
- TUI application (Textual)

The primary use case is rapid voice note taking while working in a terminal or editor.

Implementation status: initial CLI, TUI, service layer, output layer, and unit
tests are implemented in this directory.

---

# Technology Stack

- Python 3.12+
- uv
- argparse
- Textual
- Whisper (existing transcription implementation)
- Existing audio recording implementation
- pathlib
- logging
- tempfile

---

# Command Line Interface

## Executable

```bash
uv run python src/voice-note/voice-note.py
```

After `uv sync`, the project script is also available:

```bash
uv run voice-note
```

---

## Help

```bash
uv run python src/voice-note/voice-note.py --help
```

---

## Arguments

### General

```bash
--mode cli|tui
```

Default:

```text
cli
```

---

```bash
--config ./config.json
```

Optional configuration file.

---

```bash
--verbose
```

Enable debug logging.

---

### Audio

```bash
--audio-output-folder ./audio
```

Optional folder for saving recorded audio.

If omitted:

```text
temporary files are used
```

---

```bash
--keep-audio
```

Preserve recorded audio files.

Default:

```text
false
```

---

### Text Output

```bash
--text-output-file ./notes.md
```

Append transcriptions to specified file.

If omitted:

```text
print to stdout
```

---

```bash
--append-timestamp
```

Add timestamp before transcription.

Example:

```markdown
[2026-06-23 14:35:10]

Need to investigate Supabase RLS.
```

---

### Whisper

```bash
--language auto
```

or

```bash
--language en
--language ru
```

---

```bash
--model base
```

Examples:

```text
tiny
base
small
medium
large
```

---

# Operating Modes

## CLI Mode

### Startup

```bash
uv run python src/voice-note/voice-note.py --mode cli
```

Display:

```text
SPACE = start/stop recording
ESC   = exit
```

Portable terminal input does not reliably expose key release events, so CLI
mode uses SPACE as a start/stop toggle.

---

### Recording Flow

When user presses SPACE:

```text
start recording
```

When user releases SPACE:

```text
stop recording
```

Then:

```text
transcribe audio
```

Then:

```text
emit text
```

---

### Output Example

```text
> Hello world

> Create task for frontend developer

> Investigate Supabase authentication
```

---

### File Output Example

```markdown
[2026-06-23 14:35:10]

Hello world

[2026-06-23 14:36:22]

Create task for frontend developer
```

---

## TUI Mode

### Startup

```bash
uv run python src/voice-note/voice-note.py --mode tui
```

Launch Textual application.

---

### Layout

```text
┌───────────────────────────────────────┐
│ Voice Note                            │
├───────────────────────────────────────┤
│                                       │
│ Previous Notes                        │
│                                       │
│ • First note                          │
│ • Second note                         │
│                                       │
├───────────────────────────────────────┤
│ Status: Idle                          │
└───────────────────────────────────────┘
```

---

### States

#### Idle

```text
Status: Idle
```

#### Recording

```text
Status: Recording...
```

#### Transcribing

```text
Status: Transcribing...
```

#### Error

```text
Status: Error
```

---

### Keyboard Shortcuts

```text
SPACE   Start/Stop Recording
CTRL+S  Save Notes
CTRL+L  Insert Timestamp
CTRL+C  Exit
ESC     Exit
```

---

# Architecture

## Layer 1: Recorder

Responsibility:

```python
record_audio() -> Path
```

Provides:

- start recording
- stop recording
- return audio file path

Should not know anything about transcription.

---

## Layer 2: Transcriber

Responsibility:

```python
transcribe(audio_file: Path) -> str
```

Provides:

- speech-to-text conversion

Should not know anything about files or UI.

---

## Layer 3: Output Writer

Responsibility:

```python
write_text(text: str)
```

Implementations:

### StdoutWriter

```python
print(text)
```

### FileWriter

```python
append(text)
```

---

## Layer 4: Controller

Coordinates workflow.

```python
audio = recorder.record()

text = transcriber.transcribe(audio)

writer.write(text)
```

---

# Suggested Project Structure

```text
voice_note/

├── main.py

├── cli/
│   ├── parser.py
│   └── cli_app.py

├── tui/
│   ├── app.py
│   ├── widgets.py
│   └── screens.py

├── audio/
│   ├── recorder.py
│   └── devices.py

├── transcription/
│   └── whisper_transcriber.py

├── output/
│   ├── stdout_writer.py
│   └── file_writer.py

├── config/
│   └── settings.py

├── services/
│   └── voice_note_service.py

└── models/
    ├── settings.py
    └── note.py
```

---

# Configuration File Example

```json
{
  "mode": "cli",
  "language": "auto",
  "model": "base",
  "append_timestamp": true,
  "keep_audio": false,
  "audio_output_folder": "./audio",
  "text_output_file": "./notes.md"
}
```

---

# Future Extensions (Out of Scope)

- Voice Activity Detection (VAD)
- Global hotkeys
- Clipboard output
- LLM note summarization
- Speaker diarization
- Real-time streaming transcription
- Obsidian integration
- Markdown formatting
- Meeting mode
- Multiple transcription backends
- Audio device selection UI

---

# Acceptance Criteria

- Supports CLI mode
- Supports Textual TUI mode
- Records audio using push-to-talk
- Transcribes using existing Whisper implementation
- Outputs transcription to stdout
- Optionally appends transcription to file
- Supports timestamps
- Uses temporary files when audio saving is disabled
- Clean separation between Recorder, Transcriber, UI, and Output layers
- Runs via:

```bash
uv run voice-note
```

- Fully typed Python code
- No business logic inside UI layer
- Unit tests for core services

This design keeps the tool Unix-like: `audio-record` and `audio-transcribe` remain independent tools, while `voice-note` becomes a composition/orchestration layer built on top of them.

---

# Implemented Files

```text
voice_note/
├── main.py
├── cli/
├── tui/
├── audio/
├── transcription/
├── output/
├── services/
└── models/
```

---

# Checks

```bash
PYTHONPATH=src/voice-note uv run python -m compileall src/voice-note
PYTHONPATH=src/voice-note uv run python src/voice-note/voice-note.py --help
PYTHONPATH=src/voice-note uv run python -m unittest discover -s src/voice-note/tests
uv run voice-note --help
```
