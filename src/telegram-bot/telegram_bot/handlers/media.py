from __future__ import annotations

import subprocess

from aiogram import Bot, F, Router
from aiogram.types import Message

from telegram_bot.handlers.utils import split_text
from telegram_bot.services.voice_note import TelegramVoiceNoteService


def build_media_router(service: TelegramVoiceNoteService) -> Router:
    router = Router()

    @router.message(F.voice)
    async def voice(message: Message, bot: Bot) -> None:
        await _handle_audio_message(message, bot, service)

    @router.message(F.audio)
    async def audio(message: Message, bot: Bot) -> None:
        await _handle_audio_message(message, bot, service)

    return router


async def _handle_audio_message(
    message: Message,
    bot: Bot,
    service: TelegramVoiceNoteService,
) -> None:
    await message.answer("Transcribing audio...")

    try:
        result = await service.transcribe_message(bot, message)
    except ValueError as error:
        await message.answer(f"Validation error: {error}")
        return
    except FileNotFoundError as error:
        await message.answer(f"Dependency not found: {error}")
        return
    except subprocess.CalledProcessError as error:
        await message.answer(
            f"Transcription failed with exit code {error.returncode}."
        )
        return
    except RuntimeError as error:
        await message.answer(f"Voice-note error: {error}")
        return

    reply_text = service.build_transcript_message(result)
    for chunk in split_text(reply_text, service.settings.reply_chunk_size):
        await message.answer(chunk)
