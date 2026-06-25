from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.bootstrap import ensure_workspace_paths
from app.services.sessions import SessionRecord, SessionStore

ensure_workspace_paths()

from audio_record import AudioRecorder
from audio_record.models.settings import RecordingSettings


TIMESTAMP_FORMAT = "%Y_%m_%d-%H_%M_%S"


@dataclass
class MeetingRecordingSession:
    recorder: AudioRecorder
    meeting_dir: Path
    audio_file: Path
    metadata_file: Path
    timestamp: str

    def stop(self) -> Path:
        self.recorder.stop()
        return self.audio_file


class MeetingRecordingService:
    def __init__(self, store: SessionStore | None = None) -> None:
        self.store = store or SessionStore()

    def start(
        self,
        *,
        meetings_dir: Path,
        stamp: str,
        device_name: str,
        timestamp: str | None,
        verbose: bool,
    ) -> tuple[str, MeetingRecordingSession]:
        current_timestamp = timestamp or datetime.now().strftime(TIMESTAMP_FORMAT)
        self._validate_timestamp(current_timestamp)

        meeting_dir = meetings_dir / f"meeting-{current_timestamp}"
        audio_file = meeting_dir / f"meeting-core-{current_timestamp}.wav"
        metadata_file = meeting_dir / "metadata.json"
        if meeting_dir.exists():
            raise FileExistsError(meeting_dir)

        meeting_dir.mkdir(parents=True, exist_ok=False)
        self._write_metadata(metadata_file, stamp, current_timestamp)

        recorder = AudioRecorder(
            settings=RecordingSettings(
                output_file=audio_file,
                device=device_name,
                output_format="wav",
            ),
            verbose=verbose,
        )
        recorder.start()
        session = MeetingRecordingSession(
            recorder=recorder,
            meeting_dir=meeting_dir,
            audio_file=audio_file,
            metadata_file=metadata_file,
            timestamp=current_timestamp,
        )
        session_id = uuid4().hex
        self.store.add(
            SessionRecord(
                session_id=session_id,
                kind="meeting-recording",
                started_at=datetime.now(),
                payload=session,
            )
        )
        return session_id, session

    def stop(self, session_id: str) -> MeetingRecordingSession:
        session = self.store.pop(session_id)
        if session.kind != "meeting-recording":
            raise KeyError(session_id)

        payload = session.payload
        assert isinstance(payload, MeetingRecordingSession)
        payload.stop()
        return payload

    def _write_metadata(self, metadata_file: Path, stamp: str, timestamp: str) -> None:
        payload = {
            "stamp": stamp,
            "timestamp": timestamp,
        }
        metadata_file.write_text(json.dumps(payload, indent=2) + "\n")

    def _validate_timestamp(self, timestamp: str) -> None:
        try:
            datetime.strptime(timestamp, TIMESTAMP_FORMAT)
        except ValueError as error:
            raise ValueError(
                f"Timestamp must match format {TIMESTAMP_FORMAT}: {timestamp}"
            ) from error
