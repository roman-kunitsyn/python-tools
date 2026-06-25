from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from aiogram import Bot
from aiogram.types import Message

from telegram_bot.config import BotSettings
from telegram_bot.models import AudioSource, TranscriptionResult
from telegram_bot.services.conversation import ConversationStore
from telegram_bot.services.transcription import WhisperTranscriptionService


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


class TelegramVoiceNoteService:
    def __init__(
        self,
        settings: BotSettings,
        conversation_store: ConversationStore | None = None,
        transcription_service: WhisperTranscriptionService | None = None,
    ) -> None:
        self.settings = settings
        self.conversation_store = conversation_store or ConversationStore()
        self.transcription_service = transcription_service or WhisperTranscriptionService(
            model=settings.model,
            language=settings.language,
            verbose=settings.verbose,
            log_file=settings.log_file,
        )

    def start_voice_note(self, chat_id: int) -> None:
        self.conversation_store.start_voice_note(chat_id)

    def is_voice_note_active(self, chat_id: int) -> bool:
        return self.conversation_store.is_voice_note_active(chat_id)

    def build_start_message(self) -> str:
        return (
            "Send a voice message or audio file and I will transcribe it.\n"
            "Use /voice-note to mark the next message as a voice-note workflow."
        )

    def build_voice_note_prompt(self) -> str:
        return "Voice-note mode is active. Send a voice message or audio file."

    def build_transcript_message(self, result: TranscriptionResult) -> str:
        title = "Voice-note transcript" if result.active_voice_note_session else "Transcript"
        transcript = result.transcript or "(no speech detected)"
        return (
            f"{title} from {result.source.label}:\n\n"
            f"{transcript}"
        )

    async def transcribe_message(self, bot: Bot, message: Message) -> TranscriptionResult:
        source = build_audio_source(message)

        with tempfile.TemporaryDirectory(prefix="telegram-bot-") as temp_dir:
            local_file = Path(temp_dir) / source.filename
            file = await bot.get_file(source.file_id)
            if file.file_path is None:
                raise RuntimeError("Telegram file path is missing")

            await bot.download_file(file.file_path, destination=local_file)
            transcript = await asyncio.to_thread(
                self.transcription_service.transcribe,
                local_file,
            )
            active_voice_note_session = self.conversation_store.consume_voice_note(
                message.chat.id
            )
            return TranscriptionResult(
                source=source,
                local_file=local_file,
                transcript=transcript,
                active_voice_note_session=active_voice_note_session,
            )
