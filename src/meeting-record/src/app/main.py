import subprocess
import sys

from src.app.cli.parser import build_config_from_args, build_parser
from src.app.services.recorder import MeetingRecordService
from src.app.ui.app import MeetingRecordApp


def run_cli(args) -> int:
    config = build_config_from_args(args)
    service = MeetingRecordService(verbose=args.verbose)
    result = service.record(config)

    print(f"Meeting directory: {result.meeting_dir}")
    print(f"Audio file: {result.audio_file}")
    print(f"Metadata file: {result.metadata_file}")

    return 0


def run_tui(args) -> int:
    config = build_config_from_args(args)
    MeetingRecordApp(config).run()
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
    except FileExistsError as error:
        print(f"Output already exists: {error.filename}", file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        print(f"ffmpeg failed: {error}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        print(f"ffmpeg failed with exit code {error.returncode}.", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Recording interrupted.", file=sys.stderr)
        return 130
