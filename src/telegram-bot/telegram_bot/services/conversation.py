from __future__ import annotations


class ConversationStore:
    def __init__(self) -> None:
        self._active_voice_note_chats: set[int] = set()

    def start_voice_note(self, chat_id: int) -> None:
        self._active_voice_note_chats.add(chat_id)

    def consume_voice_note(self, chat_id: int) -> bool:
        if chat_id in self._active_voice_note_chats:
            self._active_voice_note_chats.remove(chat_id)
            return True

        return False

    def is_voice_note_active(self, chat_id: int) -> bool:
        return chat_id in self._active_voice_note_chats
