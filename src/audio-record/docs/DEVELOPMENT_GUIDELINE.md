# audio-record Development Guideline

## Responsibility

`audio-record` records audio from an input device and saves it to a file.

It must not transcribe, summarize, analyze, split, or modify audio after
recording. Those responsibilities belong to downstream tools.

## Architecture

- `audio-record.py` is a thin script entry point.
- `audio_record.cli` owns argument parsing and conversion to settings.
- `audio_record.models` contains small dataclass models.
- `audio_record.recorder.ffmpeg` builds and runs FFmpeg commands.
- `audio_record.recorder.devices` owns platform-specific device discovery.
- `AudioRecorder` is the high-level Python API consumed by other tools.

## Subprocess Rules

- Build FFmpeg commands as `list[str]`.
- Do not use shell execution.
- Keep platform-specific FFmpeg flags in the recorder package.
- Raise typed recorder exceptions instead of leaking subprocess details from
  public APIs.

## Return Codes

- `0`: success
- `1`: user input or device selection error
- `2`: recording failure
- `3`: environment or unsupported platform error
- `130`: interrupted by user
