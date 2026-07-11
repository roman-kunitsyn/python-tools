import logging
import sys
from dataclasses import replace

from voice_note.cli.cli_app import VoiceNoteCliApp, choose_cli_session
from voice_note.cli.parser import build_parser, build_settings_from_args
from voice_note.services.runtime import build_service
from voice_note.services.session_service import SessionService
from voice_note.tui.app import VoiceNoteApp


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        settings = build_settings_from_args(args)
        logging.basicConfig(level=logging.DEBUG if settings.verbose else logging.WARNING)

        if settings.mode == "tui":
            VoiceNoteApp(
                settings=settings,
                session_service=SessionService(timestamp_format=settings.timestamp_format),
                config_file=args.config,
            ).run()
            return 0

        session_service = SessionService(timestamp_format=settings.timestamp_format)
        if sys.stdin.isatty() and settings.session_dir is None:
            session = choose_cli_session(
                session_service=session_service,
                default_title=settings.session_title,
            )
            settings = replace(
                settings,
                session_dir=session.session_dir,
                session_title=session.title,
            )
        session = settings.with_default_storage()
        service = build_service(settings, session.session_dir)
        return VoiceNoteCliApp(
            service=service,
            max_recording_seconds=settings.max_recording_seconds,
            session_title=settings.session_title,
            session_dir=session.session_dir,
        ).run()
    except ValueError as error:
        print(f"Validation error: {error}", file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        print(f"Dependency not found: {error}", file=sys.stderr)
        return 3
    except RuntimeError as error:
        print(f"Voice note failed: {error}", file=sys.stderr)
        return 2
