# Task: Implement `audio-record` Tool

## Objective

Implement a reusable command-line audio recording utility named `audio-record`.

The tool acts as a Python wrapper around FFmpeg and provides a stable interface for other tools such as:

- voice-note
- audio-transcribe
- meeting-record
- audio-analyze
- speech-capture

The tool should hide FFmpeg complexity and expose a simple, cross-platform Python API and CLI.

---

# Technology Stack

- Python 3.12+
- uv
- argparse
- pathlib
- subprocess
- ffmpeg (external dependency)
- pydantic (optional)

---

# Design Principles

## Unix Philosophy

The tool should do one thing only:

```text
Record audio and save it to a file.
```

The tool must NOT:

- transcribe
- summarize
- analyze
- modify audio

Those responsibilities belong to other tools.

---

# CLI Interface

## Executable

```bash
audio-record
```

---

# Help

```bash
audio-record --help
```

---

# Examples

## Record until CTRL+C

```bash
audio-record output.wav
```

---

## Record from specific device

```bash
audio-record output.wav \
  --device "Built-in Microphone"
```

---

## Record for 30 seconds

```bash
audio-record output.wav \
  --duration 30
```

---

## Record to temp file

```bash
audio-record
```

Output:

```text
/tmp/audio-record-123456.wav
```

---

# Command Line Arguments

## Output

```bash
audio-record output.wav
```

Positional argument.

Optional.

If omitted:

```text
temporary file created
```

---

## Audio Device

```bash
--device "Built-in Microphone"
```

Optional.

Default:

```text
system default input device
```

---

## Duration

```bash
--duration 60
```

Optional.

Duration in seconds.

Behavior:

```text
record automatically stops after duration
```

---

## Sample Rate

```bash
--sample-rate 16000
```

Default:

```text
16000
```

---

## Channels

```bash
--channels 1
```

Default:

```text
1
```

Examples:

```text
1 = mono
2 = stereo
```

---

## Format

```bash
--format wav
```

Supported:

```text
wav
mp3
flac
m4a
```

Default:

```text
wav
```

---

## List Devices

```bash
audio-record --list-devices
```

Displays available audio input devices.

---

## Verbose

```bash
--verbose
```

Displays FFmpeg command and logs.

---

# Python API

## Recorder Class

```python
from pathlib import Path

class AudioRecorder:
    def record(
        self,
        output_file: Path,
    ) -> Path:
        ...
```

---

## Recording Session

```python
recorder = AudioRecorder()

recorder.start()

...

recorder.stop()
```

---

# Recording Modes

## Blocking Recording

```python
path = recorder.record(
    duration=10
)
```

Records for 10 seconds.

Returns file path.

---

## Push-To-Talk Recording

Required for voice-note.

```python
recorder.start()

# wait

recorder.stop()
```

Returns:

```python
Path("recording.wav")
```

---

# FFmpeg Integration

## macOS

Use:

```bash
ffmpeg \
-f avfoundation \
-i ":0" \
output.wav
```

---

## Linux

Use:

```bash
ffmpeg \
-f pulse \
-i default \
output.wav
```

or

```bash
ffmpeg \
-f alsa \
-i default \
output.wav
```

---

## Windows

Use:

```bash
ffmpeg \
-f dshow \
-i audio="Microphone" \
output.wav
```

---

# Device Discovery

## API

```python
AudioDevice
```

Model:

```python
class AudioDevice:
    id: str
    name: str
    platform: str
```

---

## List Devices

```python
devices = get_audio_devices()
```

Returns:

```python
[
    AudioDevice(
        id="0",
        name="Built-in Microphone"
    ),
]
```

---

# Project Structure

```text
audio_record/

├── main.py

├── cli/
│   └── parser.py

├── recorder/
│   ├── recorder.py
│   ├── ffmpeg.py
│   └── devices.py

├── models/
│   ├── device.py
│   └── settings.py

├── utils/
│   ├── tempfiles.py
│   └── platform.py

└── tests/
```

---

# Internal Architecture

## FFmpegCommandBuilder

Responsibility:

```python
build_ffmpeg_command()
```

Produces:

```python
[
    "ffmpeg",
    "-f",
    "avfoundation",
    ...
]
```

No execution.

---

## FFmpegRecorder

Responsibility:

```python
start()
stop()
```

Executes FFmpeg.

No CLI logic.

---

## AudioRecorder

High-level API.

Used by:

- voice-note
- meeting-record
- audio-transcribe
- tests

---

# Error Handling

## FFmpeg Missing

Raise:

```python
AudioRecorderError(
    "ffmpeg executable not found"
)
```

---

## Invalid Device

Raise:

```python
AudioDeviceNotFoundError
```

---

## Recording Failed

Raise:

```python
AudioRecordingError
```

---

# Integration Requirements

Must be usable from:

```python
from audio_record import AudioRecorder
```

Example:

```python
recorder = AudioRecorder()

audio_file = recorder.record(
    duration=5
)
```

---

# Integration With voice-note

Required workflow:

```python
recorder.start()

# user holds SPACE

audio_file = recorder.stop()

text = transcriber.transcribe(
    audio_file
)
```

No modifications should be required in voice-note when replacing FFmpeg implementation.

---

# Acceptance Criteria

- Works on macOS
- Works on Linux
- Supports FFmpeg backend
- Supports blocking recording
- Supports start/stop recording
- Supports temporary files
- Supports custom output files
- Supports audio device enumeration
- Supports device selection
- Fully typed Python code
- Unit tests for command generation
- No UI dependencies
- No transcription logic
- Can serve as a reusable library for future tools

I would also recommend a companion utility:

```text
audio-devices
```

which is just:

```bash
audio-devices
```

and outputs:

```text
[0] Built-in Microphone
[1] AirPods Pro
[2] Aggregate Device
[3] BlackHole 2ch
```

Then all your other tools (`audio-record`, `meeting-record`, `voice-note`) can reuse the same device discovery code instead of implementing `--list-devices` separately.
