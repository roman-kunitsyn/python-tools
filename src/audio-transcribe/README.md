# Audio Transcribe

Transcribe an audio file with `whisper-cli`.

## Requirements

- Python 3.10 or newer
- `uv`
- `whisper-cli` available on `PATH`
- A Whisper model file

By default, the CLI uses:

```text
~/whisper/models/ggml-small.bin
```

Override it with `--model-file` when needed.

## Usage

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

## Exit Codes

- `0`: success
- `1`: validation error
- `2`: `whisper-cli` failed
