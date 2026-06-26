from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from telegram_bot.services.voice_note import TelegramVoiceNoteService


def build_command_router(service: TelegramVoiceNoteService) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        await message.answer(service.build_start_message())

    @router.message(Command("voice-note"))
    async def voice_note(message: Message) -> None:
        service.start_voice_note(message.chat.id)
        await message.answer(service.build_voice_note_prompt())

    return router
