import subprocess
import sys

from src.app.cli.parser import build_config_from_args, build_parser
from src.app.services.transcriber import TranscribeService
from src.app.ui.app import TranscribeApp


def run_cli(args) -> int:
    config = build_config_from_args(args)
    service = TranscribeService(verbose=args.verbose)
    transcript_file = service.transcribe(config)

    if args.verbose:
        print(f"Transcription written to: {transcript_file}")

    return 0


def run_tui(args) -> int:
    config = build_config_from_args(args, require_audio_file=False)
    TranscribeApp(config).run()
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.mode == "tui":
            return run_tui(args)

        return run_cli(args)
    except ValueError as error:
        print(f"Validation error: {error}", file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        print(f"Whisper failed: {error}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        print(f"Whisper failed with exit code {error.returncode}.", file=sys.stderr)
        return 2
