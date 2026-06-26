from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from telegram_bot.handlers.utils import split_text
from telegram_bot.keyboards.menu import build_main_menu_keyboard
from telegram_bot.keyboards.voice_note import build_voice_note_keyboard
from telegram_bot.services.voice_note import TelegramVoiceNoteService
from telegram_bot.states.voice_note import VoiceNoteStates


def build_media_router(service: TelegramVoiceNoteService) -> Router:
    router = Router()

    @router.message(StateFilter(VoiceNoteStates.waiting_voice), F.voice)
    async def voice(message: Message, bot: Bot, state: FSMContext) -> None:
        await _handle_voice_message(message, bot, state, service)

    @router.message(StateFilter(VoiceNoteStates.waiting_voice), F.audio)
    async def audio(message: Message, bot: Bot, state: FSMContext) -> None:
        await _handle_voice_message(message, bot, state, service)

    @router.message(F.voice | F.audio)
    async def out_of_session(message: Message) -> None:
        if service.is_voice_note_active(message.chat.id):
            await message.answer(
                "This session is waiting for a choice. Use Add More to record again, "
                "Finish to save the note, or Cancel to discard it.",
                reply_markup=build_voice_note_keyboard(include_add_more=True),
            )
            return

        await message.answer(
            "Use /voice_note to start a voice note session.",
            reply_markup=build_main_menu_keyboard(),
        )

    return router


async def _handle_voice_message(
    message: Message,
    bot: Bot,
    state: FSMContext,
    service: TelegramVoiceNoteService,
) -> None:
    if not service.is_voice_note_active(message.chat.id):
        await state.clear()
        await message.answer(
            "Use /voice_note to start a voice note session.",
            reply_markup=build_main_menu_keyboard(),
        )
        return

    await message.answer("Transcribing voice note...")

    try:
        result = await service.process_voice_message(bot, message)
    except ValueError as error:
        await message.answer(f"Validation error: {error}")
        return
    except FileNotFoundError as error:
        await message.answer(f"Dependency not found: {error}")
        return
    except RuntimeError as error:
        await message.answer(f"Voice-note error: {error}")
        return

    await state.set_state(VoiceNoteStates.waiting_decision)
    await state.update_data(session_id=result.session.session_id, voice_index=result.entry.index)

    chunks = split_text(result.reply_text, service.settings.reply_chunk_size)
    for index, chunk in enumerate(chunks):
        await message.answer(
            chunk,
            reply_markup=build_voice_note_keyboard(include_add_more=index == len(chunks) - 1),
        )
