import logging
import sys

from voice_note.audio.recorder import PushToTalkRecorder
from voice_note.cli.cli_app import VoiceNoteCliApp
from voice_note.cli.parser import build_parser, build_settings_from_args
from voice_note.output.writer import TranscriptJsonWriter, build_writer
from voice_note.services.voice_note_service import VoiceNoteService
from voice_note.transcription.whisper_transcriber import WhisperTranscriber
from voice_note.tui.app import VoiceNoteApp


def build_service(settings) -> VoiceNoteService:
    recorder = PushToTalkRecorder(
        audio_output_folder=settings.audio_output_folder,
        audio_file=settings.audio_file,
        audio_device=settings.audio_device,
        max_recording_seconds=settings.max_recording_seconds,
        keep_audio=settings.keep_audio,
        verbose=False,
    )
    transcriber = WhisperTranscriber(
        model=settings.model,
        language=settings.language,
        verbose=settings.verbose,
        log_file=settings.log_file,
    )
    writer = build_writer(settings.text_output_file)
    json_writer = TranscriptJsonWriter(
        output_file=settings.json_output_file,
        session=settings.session_dir.name if settings.session_dir is not None else "",
    )
    return VoiceNoteService(
        recorder=recorder,
        transcriber=transcriber,
        writer=writer,
        json_writer=json_writer,
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
            VoiceNoteApp(
                service=service,
                editor=settings.editor,
                max_recording_seconds=settings.max_recording_seconds,
            ).run()
            return 0

        return VoiceNoteCliApp(
            service=service,
            max_recording_seconds=settings.max_recording_seconds,
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
