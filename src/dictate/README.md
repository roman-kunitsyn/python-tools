# Dictate

A simple command-line voice dictation tool designed to integrate naturally with terminal workflows and text editors such as Neovim.

The philosophy of this project is:

- **CLI first**
- **Editor independent**
- **Unix friendly**
- **Single responsibility**
- **Composable**

The tool records audio from the microphone, transcribes it using a local speech recognition engine, and prints the resulting text to `stdout`.

Because the transcript is written to standard output, the tool can be used from:

- Terminal
- Neovim
- VS Code
- Telegram bots
- Shell scripts
- Python applications
- CI/CD pipelines

---

# Goals

- Local-first.
- No cloud dependency.
- Fast startup.
- Minimal dependencies.
- Easy to automate.
- Easy to integrate with editors.

---

# Architecture

```text
Microphone
      │
      ▼
record_audio()
      │
      ▼
temporary .wav
      │
      ▼
transcribe()
      │
      ▼
stdout
```

The application does **not** know anything about Neovim or any editor.

It simply receives microphone input and prints text.

---

# Features

Current MVP:

- microphone recording
- temporary WAV file
- Whisper transcription
- stdout output
- optional file output
- configurable model
- configurable language

Future:

- streaming transcription
- voice activity detection (VAD)
- clipboard support
- speaker diarization
- translation
- punctuation restoration
- prompt-assisted transcription
- reusable Python API

---

# Usage

Record and print transcript:

```bash
dictate
```

Specify model:

```bash
dictate --model base
```

Specify language:

```bash
dictate --language en
```

Save transcript:

```bash
dictate --output meeting.txt
```

Verbose mode:

```bash
dictate --verbose
```

Version:

```bash
dictate --version
```

Help:

```bash
dictate --help
```

---

# Neovim Integration

No plugin is required.

Insert transcript at the cursor:

```vim
:r !dictate
```

or

```vim
:read !dictate
```

Replace selected text (future workflow):

```vim
:'<,'>!dictate
```

The editor simply launches the executable.

---

# CLI Design

The tool follows the same interface conventions as the other utilities in the toolkit.

```
--output
--verbose
--help
--version
```

Future common arguments:

```
--model
--language
--device
--format
```

---

# Project Structure

Current version:

```text
dictate.py
```

Future:

```text
dictate/
├── dictate.py
├── recorder.py
├── whisper.py
├── models.py
├── config.py
└── utils.py
```

The first implementation intentionally remains a single file.

---

# Internal Architecture

The program is organized into small reusable functions.

```text
main()
│
├── parse_args()
├── record_audio()
├── transcribe()
├── write_output()
└── cleanup()
```

Each function has a single responsibility.

---

# Recording Backend

Version 1 uses:

```
ffmpeg
```

Responsibilities:

- select microphone
- record audio
- produce temporary WAV

Future implementations may support:

- PortAudio
- PyAudio
- sounddevice

without changing the public CLI.

---

# Speech Recognition Backend

Version 1 uses:

```
whisper-cli
```

Future adapters may include:

- whisper.cpp
- whisper-server
- faster-whisper
- OpenAI Whisper
- Whisper Live
- local HTTP servers

The CLI should remain unchanged regardless of backend.

---

# Design Principles

## CLI First

Every feature must be accessible from the command line before editor integration.

---

## Editor Independent

No code should depend on Neovim APIs.

Editors are adapters, not dependencies.

---

## Unix Philosophy

Input:

- microphone

Output:

- stdout

Errors:

- stderr

Exit codes:

- standard POSIX conventions

---

## Small Functions

Prefer:

```text
record_audio()

transcribe()

write_output()
```

instead of one large function.

---

## Thin Adapters

Neovim, Telegram, and future interfaces should remain extremely small.

Example:

```
Cursor
    │
    ▼
dictate
    │
stdout
    ▼
Insert into buffer
```

---

# Implementation Plan

## Phase 1 — MVP

- [ ] Create CLI using `argparse`
- [ ] Implement microphone recording using `ffmpeg`
- [ ] Save audio to a temporary WAV file
- [ ] Invoke `whisper-cli`
- [ ] Print transcript to `stdout`
- [ ] Support `--output`
- [ ] Support `--language`
- [ ] Support `--model`
- [ ] Support `--verbose`
- [ ] Return proper exit codes

---

## Phase 2 — Better Recording

- [ ] Select recording device
- [ ] Recording timeout
- [ ] Maximum duration
- [ ] Cancel with `Ctrl+C`
- [ ] Optional WAV preservation for debugging

---

## Phase 3 — Better Transcription

- [ ] Streaming output
- [ ] Word timestamps
- [ ] Segment timestamps
- [ ] Automatic punctuation
- [ ] Confidence scores

---

## Phase 4 — Editor Workflows

- [ ] Insert at cursor
- [ ] Replace visual selection
- [ ] Dictation mode
- [ ] Voice editing commands

---

## Phase 5 — Toolkit Integration

- [ ] Shared CLI utilities
- [ ] Shared logging
- [ ] Shared configuration
- [ ] Shared LLM adapters
- [ ] Shared speech adapters

---

# Long-Term Vision

`dictate.py` is intended to become one tool in a larger collection of reusable local CLI utilities.

```text
tools/
├── dictate
├── rewrite
├── summarize
├── translate
├── grammar
├── tts
├── prompt
├── commit
└── image
```

Every tool should:

- work independently
- communicate through standard input/output where appropriate
- remain editor agnostic
- be composable with other command-line tools
- expose a clean interface for future integrations

The editor is simply another client of the toolkit, not the center of the architecture.
