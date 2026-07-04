import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from voice_note.models.session_note import SessionNote


class SessionNoteStore:
    def __init__(
        self,
        notes_file: Path,
        transcript_file: Path,
        session: str,
        append_timestamp: bool = False,
    ) -> None:
        self.notes_file = notes_file
        self.transcript_file = transcript_file
        self.session = session
        self.append_timestamp = append_timestamp

    def load_notes(self) -> list[SessionNote]:
        payload = self._read_payload()
        data = payload.get("data", [])
        notes = [self._note_from_payload(item) for item in data]
        return sorted(notes, key=lambda note: note.created_at, reverse=True)

    def get_note(self, note_id: str) -> SessionNote | None:
        for note in self.load_notes():
            if note.note_id == note_id:
                return note

        return None

    def append_note(
        self,
        text: str,
        created_at: datetime | None = None,
        audio_file: Path | None = None,
    ) -> SessionNote:
        note = SessionNote(
            note_id=uuid4().hex,
            text=text.strip(),
            created_at=created_at or datetime.now(),
            audio_file=audio_file,
        )
        notes = self.load_notes()
        notes.insert(0, note)
        self._write(notes)
        return note

    def replace_notes(self, notes: list[SessionNote]) -> None:
        ordered_notes = sorted(notes, key=lambda note: note.created_at, reverse=True)
        self._write(ordered_notes)

    def _read_payload(self) -> dict:
        if not self.notes_file.exists():
            return {"session": self.session, "data": []}

        raw = self.notes_file.read_text().strip()
        if raw == "":
            return {"session": self.session, "data": []}

        return json.loads(raw)

    def _note_from_payload(self, payload: dict) -> SessionNote:
        created_at = datetime.fromisoformat(payload["created_at"])
        audio_file = payload.get("audio_file")
        return SessionNote(
            note_id=str(payload["id"]),
            text=str(payload["text"]),
            created_at=created_at,
            audio_file=Path(audio_file) if audio_file else None,
        )

    def _write(self, notes: list[SessionNote]) -> None:
        payload = {
            "session": self.session,
            "data": [self._payload_from_note(note) for note in notes],
        }
        self.notes_file.parent.mkdir(parents=True, exist_ok=True)
        self.notes_file.write_text(json.dumps(payload, indent=2) + "\n")
        self.transcript_file.parent.mkdir(parents=True, exist_ok=True)
        self.transcript_file.write_text(self._render_transcript(notes))

    def _payload_from_note(self, note: SessionNote) -> dict:
        payload = {
            "id": note.note_id,
            "text": note.text,
            "created_at": note.created_at.isoformat(),
        }
        if note.audio_file is not None:
            payload["audio_file"] = str(note.audio_file)
        return payload

    def _render_transcript(self, notes: list[SessionNote]) -> str:
        if not notes:
            return ""

        return "\n\n".join(self._render_note(note) for note in notes) + "\n"

    def _render_note(self, note: SessionNote) -> str:
        if not self.append_timestamp:
            return note.text

        timestamp = note.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}]\n\n{note.text}"
