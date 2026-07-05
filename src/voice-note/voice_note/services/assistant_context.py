from __future__ import annotations

from dataclasses import dataclass

from voice_note.models.session_note import SessionNote


@dataclass(frozen=True)
class AssistantChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class AssistantPromptContext:
    messages: list[AssistantChatMessage]
    session_summary: str


class AssistantContextBuilder:
    def build(
        self,
        notes: list[SessionNote],
        prompt: str,
        session_title: str | None = None,
    ) -> AssistantPromptContext:
        summary = self._build_session_summary(notes, session_title)
        messages = [
            AssistantChatMessage(role="system", content=summary),
            AssistantChatMessage(role="user", content=prompt.strip()),
        ]
        return AssistantPromptContext(messages=messages, session_summary=summary)

    def _build_session_summary(
        self,
        notes: list[SessionNote],
        session_title: str | None = None,
    ) -> str:
        lines: list[str] = [
            "You are a local assistant for a voice-note session.",
            "Use the session notes as context and answer concisely unless asked otherwise.",
        ]
        if session_title:
            lines.append(f"Session title: {session_title}")

        if notes:
            lines.append("Session notes:")
            for index, note in enumerate(notes, start=1):
                note_text = note.text.strip()
                if not note_text:
                    continue
                timestamp = note.created_at.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"{index}. [{timestamp}] {note_text}")
        else:
            lines.append("Session notes: none")

        return "\n".join(lines)
