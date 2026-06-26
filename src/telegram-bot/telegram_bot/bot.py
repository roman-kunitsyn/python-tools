from __future__ import annotations

from aiogram import Dispatcher, Router

from telegram_bot.handlers.commands import build_command_router
from telegram_bot.handlers.media import build_media_router
from telegram_bot.services.voice_note import TelegramVoiceNoteService


def build_router(service: TelegramVoiceNoteService) -> Router:
    router = Router()
    router.include_router(build_command_router(service))
    router.include_router(build_media_router(service))
    return router


def build_dispatcher(service: TelegramVoiceNoteService) -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(build_router(service))
    return dispatcher
