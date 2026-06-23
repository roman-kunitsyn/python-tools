import sys

from audio_record.cli.parser import build_parser, build_settings_from_args
from audio_record.recorder.devices import get_audio_devices
from audio_record.recorder.recorder import (
    AudioDeviceNotFoundError,
    AudioRecorder,
    AudioRecorderError,
    AudioRecordingError,
)


def list_devices() -> int:
    devices = get_audio_devices()
    if not devices:
        print("No audio input devices found.")
        return 0

    for device in devices:
        print(f"{device.id}\t{device.name}\t{device.platform}")

    return 0


def run_cli(args) -> int:
    if args.list_devices:
        return list_devices()

    settings = build_settings_from_args(args)
    recorder = AudioRecorder(settings=settings, verbose=args.verbose)
    output_file = recorder.record()
    print(output_file)
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        return run_cli(args)
    except ValueError as error:
        print(f"Validation error: {error}", file=sys.stderr)
        return 1
    except AudioDeviceNotFoundError as error:
        print(f"Device error: {error}", file=sys.stderr)
        return 1
    except AudioRecordingError as error:
        print(f"Recording failed: {error}", file=sys.stderr)
        return 2
    except AudioRecorderError as error:
        print(f"Audio recorder error: {error}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("Recording interrupted.", file=sys.stderr)
        return 130
