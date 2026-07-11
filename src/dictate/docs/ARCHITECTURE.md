# Architecture

## Overview

This repository contains a collection of small, reusable command-line tools for local AI, speech, text processing, and automation.

Every tool follows the same architecture and design principles.

The goal is to make every tool usable from:

- Terminal
- Neovim
- VS Code
- Telegram bots
- FastAPI
- Python applications
- Shell scripts
- CI/CD
- Future applications

A tool should never depend on a specific editor or user interface.

---

# Architecture

```text
                   User Interfaces

        Terminal     Neovim     Telegram
            │            │            │
            └────────────┼────────────┘
                         │
                  Command Line Interface
                         │
                  Argument Parsing
                         │
                  Application Logic
                         │
             +-----------+-----------+
             |                       |
        Local Models            Local Tools
        (Ollama, etc.)      (ffmpeg, Whisper)
             |                       |
             +-----------+-----------+
                         │
                     Output
```

The CLI is the public API.

Editors are adapters.

---

# Layers

## Layer 1 — Core

Contains pure Python functions.

Example:

```python
def rewrite(text: str, prompt: str) -> str:
    ...
```

```python
def transcribe(audio: Path) -> str:
    ...
```

Rules:

- No CLI
- No argparse
- No Neovim
- No printing
- Easy to test

---

## Layer 2 — CLI

Responsible for:

- parsing arguments
- reading input
- writing output
- logging
- exit codes

The CLI should never contain business logic.

Example:

```text
stdin
    │
    ▼
read_input()
    │
    ▼
rewrite()
    │
    ▼
write_output()
```

---

## Layer 3 — Adapters

Adapters connect tools to external applications.

Examples:

- Neovim
- Telegram
- FastAPI
- Textual
- Web UI

Adapters should be extremely small.

Example:

```text
Visual Selection
        │
        ▼
rewrite
        │
stdout
        ▼
Replace selection
```

---

# Design Principles

## CLI First

Every feature must work from the terminal before editor integration.

Bad:

```text
Neovim Plugin
      │
Business Logic
```

Good:

```text
CLI
 │
Business Logic

Neovim
 │
CLI
```

---

## Editor Independent

Tools must not know which editor called them.

Avoid:

```python
if args.nvim:
    ...
```

Instead:

```python
print(result)
```

The caller decides what to do with the output.

---

## Single Responsibility

Each function should perform one task.

Good:

```text
record_audio()

transcribe()

rewrite()

write_output()
```

Avoid one large `main()` function.

---

## Thin Adapters

Adapters should contain almost no logic.

Example:

```lua
Selection
    │
rewrite
    │
Replace
```

Everything else belongs in Python.

---

## Small Commands

Each executable should solve one problem.

Good:

```text
rewrite
translate
summarize
dictate
tts
grammar
```

Avoid one executable with dozens of unrelated commands.

---

# Input Strategy

Tools should accept data from multiple sources.

Priority:

```text
1. --input
2. --file
3. stdin
4. interactive input
```

Example:

```bash
rewrite --input "Hello"

rewrite --file email.txt

cat email.txt | rewrite

rewrite
```

---

# Output Strategy

Priority:

```text
1. --output file
2. stdout
```

Output formats:

```text
text
json
```

Future:

```text
markdown
yaml
html
```

---

# Standard CLI Arguments

Every tool should support these when applicable.

```text
--help
--version
--verbose
```

Optional common arguments:

```text
--input
--prompt
--file
--output
--format
--model
--language
--device
--config
```

A consistent interface reduces cognitive load.

---

# Logging

Normal output:

```text
stdout
```

Logs:

```text
stderr
```

Example:

```bash
rewrite \
    --verbose \
    > result.txt
```

Result:

- rewritten text goes to the file
- logs stay visible

---

# Exit Codes

```text
0 Success

1 Invalid arguments

2 Input error

3 Backend unavailable

4 Runtime error
```

Never return partial or corrupted output.

---

# Error Handling

Always display human-readable errors.

Example:

```text
Error:
Unable to start Ollama.

Make sure the Ollama server is running.
```

Errors belong to `stderr`.

---

# Backends

Business logic should depend on interfaces, not implementations.

Example:

```text
rewrite()
      │
      ▼
LLM Adapter
      │
      ├── Ollama
      ├── OpenAI
      ├── LM Studio
      ├── OpenCode
      └── Future
```

Changing the backend must not change the CLI.

---

# Temporary Files

Use temporary files only when necessary.

Prefer:

```text
stdin
stdout
```

Use temporary files for:

- audio
- images
- video

in /Users/user/workspace/tools/python/logs/<app_name>/<title>-<YYYY_MM_DD-HH_MM_SS>

---

# Project Structure

/Users/user/workspace/tools/python
├── README.md
├── docs
│   ├── guidelines
│   │   ├── ARCHITECTURE_GUIDELINE.md
│   │   ├── IMPLEMENTATION_GUIDELINE.md
│   │   ├── INVESTIGATION_REVIEW_PLANNING_PROTOTYPING.md
│   │   ├── PROJECT_DOCUMENTATION_GUIDELINE.md
│   │   ├── TELEGRAM_BOT_GUIDELINE.md
│   │   ├── TESTING_GUIDELINE.md
│   │   └── UX_UI_DESIGN_GUIDELINE.md
│   ├── prompts
│   │   ├── create_audio_record.md
│   │   ├── create_browser_automation.md
│   │   ├── create_new_modular_app.md
│   │   ├── create_telegram_bot.md
│   │   ├── create_tools_api.md
│   │   └── create_voice_note.md
│   └── roles
│       ├── PRODUCT_OWNER.md
│       ├── TECHNICAL_LEAD.md
│       ├── TELEGRAM_ENGINEER.md
│       ├── TESTING_ENGINEER.md
│       ├── TOOL_ENGINEER.md
│       ├── UI_UX_DESIGNER.md
│       └── profiles
├── logs
│   ├── browser-automation
│   │   ├── boat_rental_samui-2026_06_28-13_01_11
│   │   ├── boat_rental_samui-2026_06_28-13_08_59
│   │   ├── boat_rental_samui-2026_06_28-13_25_14
│   │   ├── how_to_run.md
│   │   └── www_sontera-2026_06_28-18_22_12
│   ├── voice-generator
│   │   ├── 2026_06_30-05_52_00.wav
│   │   ├── 2026_06_30-05_53_02.wav
│   │   ├── 2026_06_30-05_53_32.wav
│   │   ├── 2026_06_30-05_53_45.wav
│   │   ├── 2026_06_30-08_10_12.wav
│   │   ├── 2026_06_30-08_12_32.wav
│   │   ├── 2026_07_01-03_23_17.wav
│   │   ├── 2026_07_01-03_27_16.wav
│   │   ├── 2026_07_01-03_31_06.wav
│   │   ├── 2026_07_01-03_35_24.wav
│   │   ├── 2026_07_01-03_37_34.wav
│   │   └── 2026_07_01-05_08_14.wav
│   └── voice_notes
│       ├── mercor_2026_07_07-12_15_11
│       ├── test_2026_07_05-23_33_52
│       ├── voice_note_2026_07_05-15_18_56
│       ├── voice_note_2026_07_06-09_44_22
│       ├── voice_note_2026_07_06-09_58_57
│       ├── voice_note_2026_07_08-10_14_55
│       ├── voice_note_2026_07_08-17_21_32
│       └── voice_note_2026_07_08-23_40_44
├── project.code-workspace
├── pyproject.toml
├── src
│   ├── api-server
│   │   ├── README.md
│   │   ├── api-server.py
│   │   ├── docs
│   │   ├── src
│   │   └── tests
│   ├── audio-record
│   │   ├── README.md
│   │   ├── audio-record.py
│   │   ├── audio_record
│   │   └── docs
│   ├── audio-transcribe
│   │   ├── README.md
│   │   ├── audio-transcribe.py
│   │   ├── docs
│   │   └── src
│   ├── browser-automation
│   │   ├── README.md
│   │   ├── browser-automation.py
│   │   ├── browser_automation
│   │   ├── docs
│   │   └── tests
│   ├── dictate
│   │   ├── README.md
│   │   ├── dictate.py
│   │   └── docs
│   ├── meeting-record
│   │   ├── README.md
│   │   ├── docs
│   │   ├── meeting-record.py
│   │   ├── meeting-split.py
│   │   ├── meeting-transcribe.py
│   │   └── src
│   ├── note-manager
│   │   ├── README.md
│   │   ├── docs
│   │   ├── note_manager.py
│   │   ├── notes.sqlite3
│   │   ├── project.code-workspace
│   │   └── task.md
│   ├── rewrite
│   │   └── rewrite.py
│   ├── schedule-manager
│   │   ├── README.md
│   │   ├── config
│   │   ├── docs
│   │   ├── graphvizs
│   │   ├── logs
│   │   ├── project.code-workspace
│   │   ├── schedule-engine.py
│   │   ├── schedules
│   │   └── sounds
│   ├── telegram-bot
│   │   ├── README.md
│   │   ├── docs
│   │   ├── telegram-bot.py
│   │   ├── telegram_bot
│   │   └── tests
│   ├── time-manager
│   │   ├── README.md
│   │   ├── audio
│   │   ├── docs
│   │   ├── project.code-workspace
│   │   └── time-manager.py
│   ├── voice-generator
│   │   ├── README.md
│   │   ├── docs
│   │   ├── tests
│   │   ├── voice-generator.py
│   │   └── voice_generator
│   └── voice-note
│       ├── README.md
│       ├── docs
│       ├── tests
│       ├── voice-note.py
│       └── voice_note
├── uv.lock
├── voice_generator
│   ├── __init__.py
│   └── __pycache__
│       └── __init__.cpython-314.pyc
└── voice_note
    ├── __init__.py
    └── __pycache__
        └── __init__.cpython-314.pyc

The first implementations may remain single-file scripts.

Refactor only when duplication becomes obvious.

---

# Testing

Test core logic independently of the CLI.

Example:

```python
def test_rewrite():
    assert rewrite("hello") == "Hello"
```

CLI tests should verify:

- arguments
- exit codes
- stdout
- stderr

---

# Neovim Integration

Neovim should call executables.

Example:

```vim
:'<,'>!rewrite
```

```vim
:r !dictate
```

No editor-specific code should exist inside the Python tools.

---

# Long-Term Vision

The toolkit should evolve into a collection of composable Unix-style utilities.

```text
tools/

rewrite
translate
summarize
grammar
dictate
tts
prompt
image
commit
ocr
clipboard
capture
```

Every executable should:

- do one thing well
- expose a consistent CLI
- be editor independent
- support automation
- compose with other tools

The CLI is the stable public interface.

Editors, bots, web applications, and future tools are simply different clients of the same architecture.
