from __future__ import annotations

from collections.abc import Sequence

from telegram_bot.models import VoiceNoteEntry


def render_voice_note_transcript_text(transcript: str) -> str:
    text = transcript.strip()
    return text if text else "(no speech detected)"


def render_finished_note_text(entries: Sequence[VoiceNoteEntry]) -> str:
    note_parts = [render_voice_note_transcript_text(entry.transcript) for entry in entries]
    return "\n\n".join(note_parts).strip() or "(no speech detected)"

