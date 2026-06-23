# audio-record Implementation Plan

## Current State

Implemented:

- CLI entry point at `audio-record.py`.
- Importable API via `from audio_record import AudioRecorder`.
- Blocking `record()` mode.
- Push-to-talk style `start()` and `stop()` mode.
- Temporary output path creation when no output path is provided.
- FFmpeg command builder with macOS, Linux, and Windows input backends.
- Audio device discovery for macOS, Windows, and best-effort Linux PulseAudio.
- Options for device, duration, sample rate, channels, format, listing devices,
  and verbose FFmpeg logs.

## Remaining Enhancements

- Add automated tests around command building and path selection.
- Add a packaging entry point named `audio-record` if this workspace becomes a
  packaged multi-tool distribution.
- Improve Linux device discovery for ALSA-only environments.
- Add TUI only if a real workflow needs it.

## Operational Dependency

Runtime recording requires `ffmpeg` on `PATH`.
