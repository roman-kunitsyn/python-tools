import logging
import sys

from voice_note.audio.recorder import PushToTalkRecorder
from voice_note.cli.cli_app import VoiceNoteCliApp
from voice_note.cli.parser import build_parser, build_settings_from_args
from voice_note.output.writer import build_writer
from voice_note.services.voice_note_service import VoiceNoteService
from voice_note.transcription.whisper_transcriber import WhisperTranscriber
from voice_note.tui.app import VoiceNoteApp


def build_service(settings) -> VoiceNoteService:
    recorder = PushToTalkRecorder(
        audio_output_folder=settings.audio_output_folder,
        audio_file=settings.audio_file,
        keep_audio=settings.keep_audio,
        verbose=settings.verbose,
    )
    transcriber = WhisperTranscriber(
        model=settings.model,
        language=settings.language,
        verbose=settings.verbose,
    )
    writer = build_writer(settings.text_output_file)
    return VoiceNoteService(
        recorder=recorder,
        transcriber=transcriber,
        writer=writer,
        append_timestamp=settings.append_timestamp,
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        settings = build_settings_from_args(args).with_default_storage()
        logging.basicConfig(level=logging.DEBUG if settings.verbose else logging.WARNING)
        service = build_service(settings)

        if settings.mode == "tui":
            VoiceNoteApp(service=service).run()
            return 0

        return VoiceNoteCliApp(service=service).run()
    except ValueError as error:
        print(f"Validation error: {error}", file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        print(f"Dependency not found: {error}", file=sys.stderr)
        return 3
    except RuntimeError as error:
        print(f"Voice note failed: {error}", file=sys.stderr)
        return 2
