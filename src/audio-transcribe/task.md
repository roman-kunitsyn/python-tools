## CLI Design

I would use:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav
```

Default:

```text
meeting.wav
↓
meeting.txt
```

---

Explicit format:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav \
  --format json
```

↓

```text
meeting.json
```

---

Custom output:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav \
  --format json \
  --output-file result
```

↓

```text
result.json
```

---

## I would remove

```python
--timestamp
```

The transcriber shouldn't know about meetings.

That's meeting-recorder responsibility.

Keep this tool focused:

```text
audio file
↓
transcription
```

---

# Proposed structure

```text
audio-transcribe/
├── audio-transcribe.py
├── constants.py
├── cli.py
├── whisper.py
└── models.py
```

For now one file is okay, but structure functions as if you'll split later.

---

# CLI API

```python
def build_parser() -> argparse.ArgumentParser:
    ...
```

```python
def validate_audio_file(audio_file: Path) -> None:
    ...
```

```python
def build_output_file(
    audio_file: Path,
    output_file: Path | None,
    output_format: str,
) -> Path:
    ...
```

```python
def get_whisper_flag(output_format: str) -> str:
    ...
```

```python
def run_whisper(
    audio_file: Path,
    output_file: Path,
    output_format: str,
    model_file: Path,
) -> None:
    ...
```

```python
def main() -> int:
    ...
```

---

# Format mapping

Avoid:

```python
if format == ...
```

Use:

```python
FORMAT_TO_FLAG = {
    "txt": "-otxt",
    "json": "-oj",
    "srt": "-osrt",
}
```

Then:

```python
flag = FORMAT_TO_FLAG[output_format]
```

---

# Validation

Example:

```python
SUPPORTED_FORMATS = {
    "txt",
    "json",
    "srt",
}
```

```python
if output_format not in SUPPORTED_FORMATS:
    raise ValueError(...)
```

---

# Output path generation

Input:

```text
meeting.wav
```

Default:

```text
meeting.txt
```

```python
audio_file.with_suffix(".txt")
```

For custom output:

```python
--output-file result
```

↓

```text
result.txt
```

---

# Whisper wrapper

Something like:

```python
command = [
    "whisper-cli",
    "-m",
    str(model_file),
    "-f",
    str(audio_file),
    "-of",
    str(output_file.with_suffix("")),
    whisper_flag,
]
```

Notice:

```python
output_file.with_suffix("")
```

because Whisper itself appends:

```text
.txt
.json
.srt
```

---

# subprocess

Use:

```python
subprocess.run(
    command,
    check=True,
)
```

instead of:

```python
capture_output=True
```

unless you actually need the output.

---

# Logging

```python
def log(message: str, verbose: bool) -> None:
    if verbose:
        print(message)
```

---

# Model path

Don't hardcode.

Default:

```python
DEFAULT_MODEL = (
    Path.home()
    / "whisper"
    / "models"
    / "ggml-small.bin"
)
```

but allow override:

```bash
--model-file ~/whisper/models/ggml-medium.bin
```

---

# argparse

I would expose:

```text
--audio-file      required
--format          default=txt
--output-file
--model-file
--language
--verbose
```

Example:

```bash
uv run audio-transcribe.py \
  --audio-file meeting.wav \
  --format json \
  --language auto \
  --verbose
```

---

# Return codes

```python
return 0
```

success

```python
return 1
```

validation error

```python
return 2
```

whisper failure

Then:

```python
raise SystemExit(main())
```

---

# Future-ready

Your meeting recorder can later call:

```python
transcribe_audio(
    audio_file=...,
    output_format="json",
)
```

instead of spawning another Python process.

That's why I would structure it as:

```python
main()
↓
transcribe_audio()
↓
run_whisper()
```

rather than putting everything at module level.

This gives you a clean CLI today and a reusable library tomorrow.
