import argparse
from pathlib import Path

from audio_record.models.settings import DEFAULT_FORMAT, RecordingSettings
from audio_record.recorder.ffmpeg import SUPPORTED_FORMATS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audio-record",
        description="Record audio from an input device with ffmpeg.",
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        help="Output audio file. If omitted, a temporary file is created.",
    )
    parser.add_argument(
        "--device",
        help="Audio input device name or id. Defaults to the system input device.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        help="Maximum recording duration in seconds.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="Sample rate in Hz. Default: 16000.",
    )
    parser.add_argument(
        "--channels",
        type=int,
        default=1,
        help="Number of audio channels. Default: 1.",
    )
    parser.add_argument(
        "--format",
        choices=sorted(SUPPORTED_FORMATS),
        default=DEFAULT_FORMAT,
        help="Output audio format. Default: wav.",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print ffmpeg command and logs.",
    )
    return parser


def build_settings_from_args(args) -> RecordingSettings:
    return RecordingSettings(
        output_file=args.output,
        device=args.device,
        duration=args.duration,
        sample_rate=args.sample_rate,
        channels=args.channels,
        output_format=args.format,
    )
