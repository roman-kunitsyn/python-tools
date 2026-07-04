from datetime import datetime
from pathlib import Path
from typing import Protocol

from voice_note.models.note import VoiceNote
from voice_note.output.session_store import SessionNoteStore
from voice_note.output.writer import TextWriter


class Recorder(Protocol):
    def start(self) -> Path:
        ...

    def stop(self) -> Path:
        ...

    def cleanup(self, audio_file: Path) -> None:
        ...


class Transcriber(Protocol):
    def transcribe(self, audio_file: Path) -> str:
        ...


class VoiceNoteService:
    def __init__(
        self,
        recorder: Recorder,
        transcriber: Transcriber,
        writer: TextWriter,
        session_store: SessionNoteStore | None = None,
        append_timestamp: bool = False,
    ) -> None:
        self.recorder = recorder
        self.transcriber = transcriber
        self.writer = writer
        self.session_store = session_store
        self.append_timestamp = append_timestamp
        self._current_audio_file: Path | None = None

    @property
    def writes_to_file(self) -> bool:
        return self.writer.writes_to_file

    @property
    def output_file(self) -> Path | None:
        if self.session_store is not None:
            return self.session_store.transcript_file

        return self.writer.output_file

    def start_recording(self) -> Path:
        if self._current_audio_file is not None:
            raise RuntimeError("recording is already running")

        self._current_audio_file = self.recorder.start()
        return self._current_audio_file

    def stop_recording_and_transcribe(self) -> VoiceNote:
        audio_file = self.recorder.stop()
        self._current_audio_file = None
        text = self.transcriber.transcribe(audio_file).strip()
        note = VoiceNote(text=text, created_at=datetime.now(), audio_file=audio_file)
        self.writer.write(format_note(note, self.append_timestamp))
        if self.session_store is not None:
            self.session_store.append_note(
                text=note.text,
                created_at=note.created_at,
                audio_file=note.audio_file,
            )
        self.recorder.cleanup(audio_file)
        return note


def format_note(note: VoiceNote, append_timestamp: bool = False) -> str:
    if not append_timestamp:
        return note.text

    timestamp = note.created_at.strftime("%Y-%m-%d %H:%M:%S")
    return f"[{timestamp}]\n\n{note.text}\n"
