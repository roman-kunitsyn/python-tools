from __future__ import annotations

from telegram_bot.models import VoiceNoteSession


class ConversationStore:
    def __init__(self) -> None:
        self._active_voice_note_sessions: dict[int, VoiceNoteSession] = {}

    def start_voice_note(self, session: VoiceNoteSession) -> None:
        self._active_voice_note_sessions[session.chat_id] = session

    def get(self, chat_id: int) -> VoiceNoteSession | None:
        return self._active_voice_note_sessions.get(chat_id)

    def remove(self, chat_id: int) -> VoiceNoteSession | None:
        return self._active_voice_note_sessions.pop(chat_id, None)

    def is_voice_note_active(self, chat_id: int) -> bool:
        return chat_id in self._active_voice_note_sessions
