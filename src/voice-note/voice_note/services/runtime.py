from pathlib import Path

from voice_note.audio.recorder import PushToTalkRecorder
from voice_note.models.settings import VoiceNoteSettings
from voice_note.output.writer import TranscriptJsonWriter, build_writer
from voice_note.services.voice_note_service import VoiceNoteService
from voice_note.transcription.whisper_transcriber import WhisperTranscriber


def build_service(
    settings: VoiceNoteSettings,
    session_dir: Path,
) -> VoiceNoteService:
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
    writer = build_writer(settings.text_output_file or session_dir / "transcribe.txt")
    json_writer = TranscriptJsonWriter(
        output_file=settings.json_output_file or session_dir / "transcribe.json",
        session=session_dir.name,
    )
    return VoiceNoteService(
        recorder=recorder,
        transcriber=transcriber,
        writer=writer,
        json_writer=json_writer,
        append_timestamp=settings.append_timestamp,
    )
