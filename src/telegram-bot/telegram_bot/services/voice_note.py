from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import Message

from telegram_bot.config import BotSettings
from telegram_bot.keyboards.voice_note import build_voice_note_keyboard
from telegram_bot.models import AudioSource, VoiceNoteEntry, VoiceNoteSession
from telegram_bot.templates.voice_note import (
    render_finished_note_text,
    render_voice_note_transcript_text,
)
from telegram_bot.services.conversation import ConversationStore
from telegram_bot.services.storage_service import VoiceNoteStorageService
from telegram_bot.services.transcription import WhisperTranscriptionService

logger = logging.getLogger(__name__)


def build_audio_source(message: Message) -> AudioSource:
    if message.voice is not None:
        return AudioSource(
            kind="voice",
            file_id=message.voice.file_id,
            filename=f"voice_{message.message_id}.ogg",
            label="voice message",
        )

    if message.audio is not None:
        filename = message.audio.file_name or f"audio_{message.message_id}.mp3"
        return AudioSource(
            kind="audio",
            file_id=message.audio.file_id,
            filename=Path(filename).name,
            label=message.audio.title or "audio file",
        )

    raise ValueError("message does not contain audio")


@dataclass(frozen=True)
class VoiceNoteProcessingResult:
    session: VoiceNoteSession
    entry: VoiceNoteEntry
    reply_text: str


@dataclass(frozen=True)
class VoiceNoteFinishResult:
    session: VoiceNoteSession
    transcript_file: Path
    transcript_text: str
    voice_count: int
    total_duration_seconds: float
    character_count: int


class TelegramVoiceNoteService:
    def __init__(
        self,
        settings: BotSettings,
        conversation_store: ConversationStore | None = None,
        transcription_service: WhisperTranscriptionService | None = None,
        storage_service: VoiceNoteStorageService | None = None,
    ) -> None:
        self.settings = settings
        self.conversation_store = conversation_store or ConversationStore()
        self.storage_service = storage_service or VoiceNoteStorageService(settings)
        self.transcription_service = transcription_service or WhisperTranscriptionService(
            model=settings.model,
            language=settings.language,
            verbose=settings.verbose,
            log_file=settings.log_file,
        )

    def get_active_session(self, chat_id: int) -> VoiceNoteSession | None:
        return self.conversation_store.get(chat_id)

    def is_voice_note_active(self, chat_id: int) -> bool:
        return self.conversation_store.is_voice_note_active(chat_id)

    async def start_session(self, message: Message) -> VoiceNoteSession:
        if message.from_user is None:
            raise ValueError("message has no user context")

        if self.is_voice_note_active(message.chat.id):
            raise ValueError("voice-note session is already active")

        session = self.storage_service.create_session(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
        )
        self.conversation_store.start_voice_note(session)
        logger.info(
            "voice_note_session_started chat_id=%s user_id=%s session_id=%s",
            session.chat_id,
            session.user_id,
            session.session_id,
        )
        return session

    def build_start_message(self) -> str:
        return (
            "🎤 Voice Note Session Started\n\n"
            "Send one or more voice messages.\n\n"
            "When finished press:\n\n"
            "✅ Finish"
        )

    def build_help_message(self, has_active_session: bool = False) -> str:
        if has_active_session:
            return (
                "Voice Note Help\n\n"
                "Send voice messages to add them to the current session.\n"
                "Use Add More to keep recording, Finish to save the note, "
                "or Cancel to discard it."
            )

        return (
            "Help\n\n"
            "/start - show the menu\n"
            "/voice_note - start a voice note session\n"
            "/cancel - cancel the active session\n"
        )

    def build_menu_message(self) -> str:
        return (
            "Menu\n\n"
            "Use /voice_note to start a new voice note session."
        )

    def build_waiting_voice_message(self) -> str:
        return "Voice Note Session Started\n\nSend one or more voice messages."

    def build_waiting_decision_message(self, entry: VoiceNoteEntry) -> str:
        return render_voice_note_transcript_text(entry.transcript)

    def build_finished_message(self, result: VoiceNoteFinishResult) -> str:
        return result.transcript_text

    def build_cancel_message(self) -> str:
        return "Voice Note Session Cancelled"

    def build_session_keyboard(self, include_add_more: bool) -> InlineKeyboardMarkup:
        return build_voice_note_keyboard(include_add_more=include_add_more)

    async def process_voice_message(
        self,
        bot: Bot,
        message: Message,
    ) -> VoiceNoteProcessingResult:
        session = self._require_session(message.chat.id)
        source = build_audio_source(message)
        index = len(session.entries) + 1
        source_file = session.audio_dir / self._build_source_filename(index, source.filename)

        await self.storage_service.download_audio(bot, source, source_file)
        wav_file = await self.storage_service.convert_to_wav(source_file)
        transcript_file = session.session_dir / f"transcript_{index:03d}.md"
        transcript = await self.transcription_service.transcribe(wav_file, transcript_file)
        duration_seconds = await asyncio.to_thread(self._wav_duration_seconds, wav_file)

        entry = VoiceNoteEntry(
            index=index,
            source_file=source_file,
            wav_file=wav_file,
            transcript_file=transcript_file,
            transcript=transcript,
            duration_seconds=duration_seconds,
        )
        session.entries.append(entry)
        await self.storage_service.append_transcript(session, entry)

        logger.info(
            "voice_note_message_processed chat_id=%s user_id=%s session_id=%s index=%s",
            session.chat_id,
            session.user_id,
            session.session_id,
            entry.index,
        )
        return VoiceNoteProcessingResult(
            session=session,
            entry=entry,
            reply_text=self.build_waiting_decision_message(entry),
        )

    async def finish_session(self, chat_id: int) -> VoiceNoteFinishResult:
        session = self._require_session(chat_id)
        transcript_file = await self.storage_service.finalize_session(session)
        transcript_text = render_finished_note_text(session.entries)
        voice_count = len(session.entries)
        total_duration_seconds = sum((entry.duration_seconds or 0.0) for entry in session.entries)
        character_count = sum(len(entry.transcript.strip()) for entry in session.entries)
        self.conversation_store.remove(chat_id)
        logger.info(
            "voice_note_session_finished chat_id=%s user_id=%s session_id=%s voices=%s",
            session.chat_id,
            session.user_id,
            session.session_id,
            voice_count,
        )
        return VoiceNoteFinishResult(
            session=session,
            transcript_file=transcript_file,
            transcript_text=transcript_text,
            voice_count=voice_count,
            total_duration_seconds=total_duration_seconds,
            character_count=character_count,
        )

    async def cancel_session(self, chat_id: int) -> None:
        session = self._require_session(chat_id)
        await self.storage_service.cancel_session(session)
        self.conversation_store.remove(chat_id)
        logger.info(
            "voice_note_session_cancelled chat_id=%s user_id=%s session_id=%s",
            session.chat_id,
            session.user_id,
            session.session_id,
        )

    def _require_session(self, chat_id: int) -> VoiceNoteSession:
        session = self.conversation_store.get(chat_id)
        if session is None:
            raise ValueError("no active voice-note session")
        return session

    def _build_source_filename(self, index: int, filename: str) -> str:
        suffix = Path(filename).suffix or ".ogg"
        return f"voice_{index:03d}{suffix}"

    def _wav_duration_seconds(self, wav_file: Path) -> float:
        import wave
        from contextlib import closing

        with closing(wave.open(str(wav_file), "rb")) as wf:
            frame_count = wf.getnframes()
            frame_rate = wf.getframerate()
            if frame_rate <= 0:
                return 0.0
            return frame_count / float(frame_rate)
