# Audio Transcribe

Transcribe an audio file with `whisper-cli` from either a CLI or a Textual TUI.

## Requirements

- Python 3.10 or newer
- `uv`
- `whisper-cli` available on `PATH`
- A Whisper model file
- `textual`, already listed in the parent Python project dependencies

By default, the CLI uses:

```text
~/whisper/models/ggml-small.bin
```

Override it with `--model-file` when needed.

## CLI Usage

Create a text transcript next to the source audio file:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav
```

This writes:

```text
meeting.txt
```

Create JSON output:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav \
  --format json
```

This writes:

```text
meeting.json
```

Create SRT subtitle output:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav \
  --format srt
```

This writes:

```text
meeting.srt
```

Use a custom output file base name:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav \
  --format json \
  --output-file result
```

This writes:

```text
result.json
```

Use a custom model:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav \
  --model-file ~/whisper/models/ggml-medium.bin
```

Set a known language instead of auto-detection:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav \
  --language en
```

Print the `whisper-cli` command before running it:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav \
  --verbose
```

## TUI Usage

Start the Textual interface:

```bash
uv run audio-transcribe.py \
  --mode tui
```

Start the TUI with fields pre-filled from CLI arguments:

```bash
uv run audio-transcribe.py \
  --mode tui \
  --audio-file meeting.wav \
  --format json \
  --language en
```

The TUI edits the same transcription config used by CLI mode, then passes it to the same service layer.

## Project Structure

```text
audio-transcribe/
├── audio-transcribe.py
├── src/
│   └── app/
│       ├── cli/
│       ├── models/
│       ├── services/
│       └── ui/
├── docs/
└── README.md
```

`audio-transcribe.py` is only the script entry point. Application behavior lives in `src/app`.

## Exit Codes

- `0`: success
- `1`: validation error
- `2`: `whisper-cli` failed
