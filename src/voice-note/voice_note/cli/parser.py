import argparse
from pathlib import Path

from voice_note.models.settings import VoiceNoteSettings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voice-note",
        description="Capture push-to-talk voice notes and transcribe them.",
    )
    parser.add_argument(
        "--mode",
        choices=("cli", "tui"),
        default=None,
        help="Run in command-line mode or Textual TUI mode.",
    )
    parser.add_argument("--config", type=Path, help="Optional JSON configuration file.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    parser.add_argument(
        "--audio-output-folder",
        type=Path,
        help="Folder for saved audio. Default: logs/voice_notes/<session>/audio.",
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="Preserve recorded audio files after transcription.",
    )
    parser.add_argument(
        "--text-output-file",
        type=Path,
        help="File where transcriptions are appended. Default: logs/voice_notes/<session>/transcribe.txt.",
    )
    parser.add_argument(
        "--append-timestamp",
        action="store_true",
        help="Write a timestamp before each transcription.",
    )
    parser.add_argument("--language", default=None, help="Whisper language. Default: auto.")
    parser.add_argument("--model", default=None, help="Whisper model name or file path.")
    return parser


def build_settings_from_args(args) -> VoiceNoteSettings:
    settings = VoiceNoteSettings.from_file(args.config) if args.config else VoiceNoteSettings()

    updates = {
        "mode": args.mode or settings.mode,
        "verbose": args.verbose or settings.verbose,
        "audio_output_folder": args.audio_output_folder or settings.audio_output_folder,
        "keep_audio": args.keep_audio or settings.keep_audio,
        "text_output_file": args.text_output_file or settings.text_output_file,
        "append_timestamp": args.append_timestamp or settings.append_timestamp,
        "language": args.language or settings.language,
        "model": args.model or settings.model,
        "session_dir": settings.session_dir,
        "audio_file": settings.audio_file,
        "log_file": settings.log_file,
    }
    return VoiceNoteSettings(**updates)
