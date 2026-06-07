import argparse
from pathlib import Path

from src.app.models.config import DEFAULT_MODEL, TranscribeConfig
from src.app.services.transcriber import SUPPORTED_FORMATS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transcribe an audio file with whisper-cli."
    )
    parser.add_argument(
        "--mode",
        choices=("cli", "tui"),
        default="cli",
        help="Run in command-line mode or Textual TUI mode.",
    )
    parser.add_argument(
        "--audio-file",
        type=Path,
        help="Path to the source audio file.",
    )
    parser.add_argument(
        "--format",
        default="txt",
        help=f"Transcription output format. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="Output file path. The selected format extension is applied automatically.",
    )
    parser.add_argument(
        "--model-file",
        type=Path,
        default=DEFAULT_MODEL,
        help=f"Path to the Whisper model file. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--language",
        default="auto",
        help="Language passed to whisper-cli. Use 'auto' for auto-detection.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print command details before running whisper-cli.",
    )
    return parser


def build_config_from_args(args, require_audio_file: bool = True) -> TranscribeConfig:
    if require_audio_file and args.audio_file is None:
        raise ValueError("--audio-file is required in CLI mode")

    return TranscribeConfig(
        audio_file=args.audio_file,
        output_file=args.output_file,
        output_format=args.format,
        model_file=args.model_file,
        language=args.language,
    )
