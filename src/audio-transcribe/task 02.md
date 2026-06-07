I think this is exactly the right moment to separate:

```text
Application Logic
    ↓
UI Layer
```

Most people make the mistake of writing:

```text
Textual App
    ↓
calls ffmpeg
calls whisper
parses files
```

and later cannot reuse anything.

---

# Architecture I would use

```text
src/
│
├── app/
│   ├── main.py
│   │
│   ├── cli/
│   │   └── parser.py
│   │
│   ├── services/
│   │   ├── transcriber.py
│   │   └── whisper.py
│   │
│   ├── models/
│   │   └── config.py
│   │
│   └── ui/
│       ├── app.py
│       │
│       ├── screens/
│       │   └── transcribe_screen.py
│       │
│       ├── widgets/
│       │   ├── file_picker.py
│       │   ├── form_field.py
│       │   ├── path_input.py
│       │   └── footer_bar.py
│       │
│       └── forms/
│           └── transcribe_form.py
│
└── pyproject.toml
```

---

# Critical design idea

Everything should revolve around one model.

```python
@dataclass
class TranscribeConfig:
    audio_file: Path
    output_file: Path | None
    output_format: str
    model_file: Path
    language: str
```

---

CLI fills it:

```text
argparse
    ↓
TranscribeConfig
```

---

TUI fills it:

```text
Textual Form
    ↓
TranscribeConfig
```

---

Business logic receives:

```text
TranscribeConfig
    ↓
transcribe()
```

---

No UI-specific code.

---

# Entry point

```bash
uv run audio-transcribe.py
```

↓

```text
CLI mode
```

---

```bash
uv run audio-transcribe.py --mode tui
```

↓

```text
Textual mode
```

---

# Reusing CLI args in TUI

This is actually very elegant.

Example:

```bash
uv run audio-transcribe.py \
    --mode tui \
    --audio-file test.wav \
    --format json
```

Textual starts with:

```text
Audio File:
[test.wav]

Format:
[json]
```

already filled.

---

Implementation:

```python
config = build_config_from_args(args)

TranscribeApp(config).run()
```

---

# Textual App

```python
class TranscribeApp(App):
    def __init__(self, config):
        super().__init__()
        self.config = config
```

---

Screen:

```python
class TranscribeScreen(Screen):
    pass
```

Fields populated from:

```python
self.app.config
```

---

# Reusable widgets

I would not use raw Input everywhere.

Build components.

---

## PathInput

```text
Audio File

[________________]

[F3 Browse]
```

Reusable.

---

## SelectField

```text
Format

[ json ▼ ]
```

Reusable.

---

## ActionButtons

```text
[F5 Start]

[Esc Cancel]
```

Reusable.

---

# File picker

Sooner or later you will need:

```text
Browse files
Browse folders
```

I would create:

```python
PathPickerScreen
```

once.

Then reuse it everywhere.

---

# Future system

Today:

```text
Audio Transcriber
```

Tomorrow:

```text
Meeting Recorder
```

Later:

```text
Voice Notes
```

Later:

```text
Meeting Manager
```

All of them need:

```text
PathInput
SelectField
ConfirmDialog
ProgressScreen
```

---

# Screens

Think in screens.

Not forms.

Example:

```text
HomeScreen

TranscribeScreen

RecordMeetingScreen

SettingsScreen
```

---

# Progress screen

Whisper can take minutes.

You will want:

```text
Transcribing...

██████████░░░░░░░░
```

Later.

So:

```python
class ProgressScreen(Screen):
    pass
```

---

# Recommended workflow

```text
argparse
        ↓
TranscribeConfig
        ↓

+------------------+
| CLI              |
+------------------+

or

+------------------+
| Textual          |
+------------------+

        ↓

TranscribeService

        ↓

WhisperWrapper

        ↓

Files
```

---

For somebody building a larger ecosystem (meeting recorder, note manager, scheduler, personal assistant) I would treat Textual as a presentation layer only.

The moment you start putting `subprocess.run("whisper-cli")` directly inside widgets or screens, technical debt starts accumulating. Keep all ffmpeg/whisper/file logic in services and let Textual only edit and display a `TranscribeConfig`. That design scales extremely well as the system grows.
