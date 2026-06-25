from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any


@dataclass
class SessionRecord:
    session_id: str
    kind: str
    started_at: datetime
    payload: Any


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self._lock = Lock()

    def add(self, session: SessionRecord) -> SessionRecord:
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def pop(self, session_id: str) -> SessionRecord:
        with self._lock:
            try:
                return self._sessions.pop(session_id)
            except KeyError as error:
                raise KeyError(session_id) from error

    def list(self) -> list[SessionRecord]:
        with self._lock:
            return list(self._sessions.values())
