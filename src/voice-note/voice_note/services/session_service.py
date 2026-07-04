import json
from datetime import datetime
from pathlib import Path

from voice_note.models.session import (
    DEFAULT_SESSION_TITLE,
    VoiceNoteSession,
    build_session_folder_name,
    parse_session_folder_name,
    slugify_session_title,
)
from voice_note.models.settings import DEFAULT_VOICE_NOTES_DIR, TIMESTAMP_FORMAT


class SessionService:
    def __init__(self, base_dir: Path = DEFAULT_VOICE_NOTES_DIR) -> None:
        self.base_dir = base_dir

    def discover_sessions(self) -> list[VoiceNoteSession]:
        if not self.base_dir.exists():
            return []

        sessions: list[VoiceNoteSession] = []
        for session_dir in self.base_dir.iterdir():
            if not session_dir.is_dir():
                continue

            session = self.load_session(session_dir)
            if session is not None:
                sessions.append(session)

        return sorted(sessions, key=_session_sort_key, reverse=True)

    def create_session(
        self,
        title: str | None = None,
        timestamp: str | None = None,
    ) -> VoiceNoteSession:
        timestamp = timestamp or datetime.now().strftime(TIMESTAMP_FORMAT)
        title = (title or DEFAULT_SESSION_TITLE).strip() or DEFAULT_SESSION_TITLE
        slug = slugify_session_title(title)
        session_dir = self.base_dir / build_session_folder_name(title, timestamp)

        session_dir.mkdir(parents=True, exist_ok=False)
        session = VoiceNoteSession(
            title=title,
            slug=slug,
            timestamp=timestamp,
            session_dir=session_dir,
        )
        self._initialize_session(session)
        return session

    def load_session(self, session_dir: Path) -> VoiceNoteSession | None:
        if not session_dir.is_dir():
            return None

        payload = self._read_metadata(session_dir)
        if payload is not None:
            return self._session_from_payload(session_dir, payload)

        parsed = parse_session_folder_name(session_dir.name)
        if parsed is None:
            return None

        slug, timestamp = parsed
        return VoiceNoteSession(
            title=slug.replace("-", " ").replace("_", " "),
            slug=slug,
            timestamp=timestamp,
            session_dir=session_dir,
        )

    def rename_session(
        self,
        session: VoiceNoteSession,
        title: str,
    ) -> VoiceNoteSession:
        normalized_title = (title or DEFAULT_SESSION_TITLE).strip() or DEFAULT_SESSION_TITLE
        slug = slugify_session_title(normalized_title)
        new_session_dir = self.base_dir / build_session_folder_name(
            normalized_title,
            session.timestamp,
        )

        if new_session_dir != session.session_dir:
            session.session_dir.rename(new_session_dir)

        renamed = VoiceNoteSession(
            title=normalized_title,
            slug=slug,
            timestamp=session.timestamp,
            session_dir=new_session_dir,
        )
        self._write_metadata(renamed)
        return renamed

    def _initialize_session(self, session: VoiceNoteSession) -> None:
        session.audio_dir.mkdir(parents=True, exist_ok=True)
        self._write_metadata(session)
        session.transcript_file.touch(exist_ok=True)
        session.transcript_json_file.touch(exist_ok=True)
        session.log_file.touch(exist_ok=True)

    def _read_metadata(self, session_dir: Path) -> dict | None:
        metadata_file = session_dir / "session.json"
        if not metadata_file.exists():
            return None

        return json.loads(metadata_file.read_text())

    def _session_from_payload(
        self,
        session_dir: Path,
        payload: dict,
    ) -> VoiceNoteSession:
        title = str(payload.get("title", DEFAULT_SESSION_TITLE)).strip() or DEFAULT_SESSION_TITLE
        slug = str(payload.get("slug", slugify_session_title(title))).strip()
        timestamp = str(payload.get("timestamp", "")).strip()
        if not timestamp:
            parsed = parse_session_folder_name(session_dir.name)
            timestamp = parsed[1] if parsed is not None else datetime.now().strftime(TIMESTAMP_FORMAT)

        return VoiceNoteSession(
            title=title,
            slug=slug,
            timestamp=timestamp,
            session_dir=session_dir,
        )

    def _write_metadata(self, session: VoiceNoteSession) -> None:
        payload = {
            "title": session.title,
            "slug": session.slug,
            "timestamp": session.timestamp,
            "folder_name": session.folder_name,
        }
        session.metadata_file.write_text(json.dumps(payload, indent=2) + "\n")


def _session_sort_key(session: VoiceNoteSession) -> tuple[str, str]:
    return session.timestamp, session.folder_name
