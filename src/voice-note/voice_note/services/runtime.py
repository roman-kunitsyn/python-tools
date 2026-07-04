from pathlib import Path

from voice_note.audio.recorder import PushToTalkRecorder
from voice_note.models.settings import VoiceNoteSettings
from voice_note.output.session_store import SessionNoteStore
from voice_note.output.writer import NullWriter, StdoutWriter
from voice_note.services.voice_note_service import VoiceNoteService
from voice_note.transcription.whisper_transcriber import WhisperTranscriber


def build_service(
    settings: VoiceNoteSettings,
    session_dir: Path,
) -> VoiceNoteService:
    session_store = SessionNoteStore(
        notes_file=settings.json_output_file or session_dir / "notes.json",
        transcript_file=settings.text_output_file or session_dir / "transcribe.txt",
        session=session_dir.name,
        append_timestamp=settings.append_timestamp,
    )
    writer = NullWriter() if settings.mode == "tui" else StdoutWriter()
    recorder = PushToTalkRecorder(
        audio_output_folder=settings.audio_output_folder or session_dir / "audio",
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
        log_file=settings.log_file or session_dir / "log.txt",
    )
    return VoiceNoteService(
        recorder=recorder,
        transcriber=transcriber,
        writer=writer,
        session_store=session_store,
        append_timestamp=settings.append_timestamp,
    )
