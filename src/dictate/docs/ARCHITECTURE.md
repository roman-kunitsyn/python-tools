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

Current:

```text
rewrite.py

dictate.py

tts.py
```

Future:

```text
tools/
├── rewrite/
│   ├── cli.py
│   ├── core.py
│   └── prompts.py
│
├── dictate/
│   ├── cli.py
│   ├── recorder.py
│   └── whisper.py
│
├── tts/
│
└── shared/
    ├── io.py
    ├── logging.py
    ├── config.py
    ├── adapters.py
    └── cli.py
```

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
