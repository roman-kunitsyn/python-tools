from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.bootstrap import ensure_workspace_paths
from app.services.sessions import SessionRecord, SessionStore

ensure_workspace_paths()

from audio_record import AudioRecorder
from audio_record.models.settings import RecordingSettings


@dataclass
class AudioRecordingSession:
    recorder: AudioRecorder
    output_file: Path

    def stop(self) -> Path:
        return self.recorder.stop()


class AudioRecordingService:
    def __init__(self, store: SessionStore | None = None) -> None:
        self.store = store or SessionStore()

    def start(
        self,
        *,
        output_file: Path | None,
        device: str | None,
        duration: float | None,
        sample_rate: int,
        channels: int,
        output_format: str,
        verbose: bool,
    ) -> tuple[str, Path]:
        recorder = AudioRecorder(
            settings=RecordingSettings(
                output_file=output_file,
                device=device,
                duration=duration,
                sample_rate=sample_rate,
                channels=channels,
                output_format=output_format,
            ),
            verbose=verbose,
        )
        target = recorder.start()
        session_id = uuid4().hex
        self.store.add(
            SessionRecord(
                session_id=session_id,
                kind="audio-recording",
                started_at=datetime.now(),
                payload=AudioRecordingSession(recorder=recorder, output_file=target),
            )
        )
        return session_id, target

    def stop(self, session_id: str) -> Path:
        session = self.store.pop(session_id)
        if session.kind != "audio-recording":
            raise KeyError(session_id)

        payload = session.payload
        assert isinstance(payload, AudioRecordingSession)
        return payload.stop()
