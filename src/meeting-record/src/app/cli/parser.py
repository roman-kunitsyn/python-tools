import argparse
from pathlib import Path

from src.app.models.config import (
    DEFAULT_DEVICE_NAME,
    DEFAULT_MEETINGS_DIR,
    RecordConfig,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record a meeting audio session with ffmpeg."
    )
    parser.add_argument(
        "--stamp",
        default="",
        help="Optional meeting label written to metadata.json.",
    )
    parser.add_argument(
        "--meetings-dir",
        type=Path,
        default=DEFAULT_MEETINGS_DIR,
        help=f"Directory where meeting folders are created. Default: {DEFAULT_MEETINGS_DIR}",
    )
    parser.add_argument(
        "--device-name",
        default=DEFAULT_DEVICE_NAME,
        help=f"Audio input device name to find in ffmpeg device output. Default: {DEFAULT_DEVICE_NAME}",
    )
    parser.add_argument(
        "--timestamp",
        help="Override timestamp for deterministic output paths.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print ffmpeg command details before recording.",
    )
    return parser


def build_config_from_args(args) -> RecordConfig:
    return RecordConfig(
        meetings_dir=args.meetings_dir,
        stamp=args.stamp,
        device_name=args.device_name,
        timestamp=args.timestamp,
    )
