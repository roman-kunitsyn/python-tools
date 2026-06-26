from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.bootstrap import ensure_workspace_paths
from app.services.sessions import SessionRecord, SessionStore

ensure_workspace_paths()

from voice_note.audio.recorder import PushToTalkRecorder
from voice_note.models.note import VoiceNote
from voice_note.models.settings import DEFAULT_VOICE_NOTES_DIR, VoiceNoteSettings
from voice_note.output.writer import TranscriptJsonWriter, build_writer
from voice_note.services.voice_note_service import format_note
from voice_note.transcription.whisper_transcriber import WhisperTranscriber


@dataclass
class VoiceNoteSession:
    recorder: PushToTalkRecorder
    transcriber: WhisperTranscriber
    writer: object
    json_writer: TranscriptJsonWriter | None
    append_timestamp: bool
    session_dir: Path | None
    audio_file: Path | None
    text_output_file: Path | None
    json_output_file: Path | None
    log_file: Path | None
    keep_audio: bool

    def stop(self) -> tuple[Path, str]:
        audio_file = self.recorder.stop()
        text = self.transcriber.transcribe(audio_file).strip()
        note = VoiceNote(text=text, created_at=datetime.now(), audio_file=audio_file)
        self.writer.write(format_note(note, self.append_timestamp))
        if self.json_writer is not None:
            self.json_writer.write_note(note)
        self.recorder.cleanup(audio_file)
        return audio_file, text


class VoiceNoteService:
    def __init__(self, store: SessionStore | None = None) -> None:
        self.store = store or SessionStore()

    def start(
        self,
        *,
        audio_output_folder: Path | None,
        keep_audio: bool,
        text_output_file: Path | None,
        json_output_file: Path | None,
        append_timestamp: bool,
        language: str,
        model: str,
        verbose: bool,
        session_dir: Path | None,
        audio_file: Path | None,
        audio_device: str | None,
        max_recording_seconds: int,
    ) -> tuple[str, VoiceNoteSession]:
        settings = VoiceNoteSettings(
            audio_output_folder=audio_output_folder,
            keep_audio=keep_audio,
            text_output_file=text_output_file,
            json_output_file=json_output_file,
            append_timestamp=append_timestamp,
            language=language,
            model=model,
            verbose=verbose,
            session_dir=session_dir,
            audio_file=audio_file,
            audio_device=audio_device,
            max_recording_seconds=max_recording_seconds,
        ).with_default_storage(base_dir=DEFAULT_VOICE_NOTES_DIR)
        settings.validate()

        recorder = PushToTalkRecorder(
            audio_output_folder=settings.audio_output_folder,
            audio_file=settings.audio_file,
            audio_device=settings.audio_device,
            max_recording_seconds=settings.max_recording_seconds,
            keep_audio=settings.keep_audio,
            verbose=settings.verbose,
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
        session = VoiceNoteSession(
            recorder=recorder,
            transcriber=transcriber,
            writer=writer,
            json_writer=json_writer,
            append_timestamp=settings.append_timestamp,
            session_dir=settings.session_dir,
            audio_file=None,
            text_output_file=settings.text_output_file,
            json_output_file=settings.json_output_file,
            log_file=settings.log_file,
            keep_audio=settings.keep_audio,
        )
        audio_file_path = session.recorder.start()
        session.audio_file = audio_file_path
        session_id = uuid4().hex
        self.store.add(
            SessionRecord(
                session_id=session_id,
                kind="voice-note",
                started_at=datetime.now(),
                payload=session,
            )
        )
        return session_id, session

    def stop(self, session_id: str) -> tuple[VoiceNoteSession, Path, str]:
        session = self.store.pop(session_id)
        if session.kind != "voice-note":
            raise KeyError(session_id)

        payload = session.payload
        assert isinstance(payload, VoiceNoteSession)
        audio_file, text = payload.stop()
        return payload, audio_file, text
