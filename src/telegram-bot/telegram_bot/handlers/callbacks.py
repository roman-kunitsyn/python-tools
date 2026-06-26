from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from telegram_bot.keyboards.menu import build_main_menu_keyboard
from telegram_bot.keyboards.voice_note import (
    ADD_MORE_CALLBACK,
    CANCEL_CALLBACK,
    FINISH_CALLBACK,
    build_voice_note_keyboard,
)
from telegram_bot.services.voice_note import TelegramVoiceNoteService
from telegram_bot.states.voice_note import VoiceNoteStates


def build_callback_router(service: TelegramVoiceNoteService) -> Router:
    router = Router()

    @router.callback_query(F.data == "menu:help")
    async def menu_help(callback: CallbackQuery) -> None:
        await callback.answer()
        if callback.message is not None:
            await callback.message.answer(
                service.build_help_message(service.is_voice_note_active(callback.message.chat.id)),
                reply_markup=build_main_menu_keyboard(),
            )

    @router.callback_query(F.data == "menu:voice_note")
    async def menu_voice_note(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        if callback.message is None:
            return
        if service.is_voice_note_active(callback.message.chat.id):
            await callback.message.answer(
                "A voice note session is already active.",
                reply_markup=build_voice_note_keyboard(include_add_more=True),
            )
            return

        session = await service.start_session(callback.message)
        await state.set_state(VoiceNoteStates.waiting_voice)
        await state.update_data(session_id=session.session_id)
        await callback.message.answer(
            service.build_start_message(),
            reply_markup=build_voice_note_keyboard(include_add_more=False),
        )

    @router.callback_query(F.data == ADD_MORE_CALLBACK)
    async def add_more(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        if callback.message is None:
            return
        if not service.is_voice_note_active(callback.message.chat.id):
            await callback.message.answer(
                "Start a voice note session first.",
                reply_markup=build_main_menu_keyboard(),
            )
            await state.clear()
            return

        await state.set_state(VoiceNoteStates.waiting_voice)
        await callback.message.answer(
            "Send the next voice message.",
            reply_markup=build_voice_note_keyboard(include_add_more=False),
        )

    @router.callback_query(F.data == FINISH_CALLBACK)
    async def finish(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        if callback.message is None:
            return
        if not service.is_voice_note_active(callback.message.chat.id):
            await state.clear()
            await callback.message.answer(
                "No active voice note session.",
                reply_markup=build_main_menu_keyboard(),
            )
            return

        result = await service.finish_session(callback.message.chat.id)
        await state.clear()
        await callback.message.answer(
            service.build_finished_message(result),
            reply_markup=build_main_menu_keyboard(),
        )

    @router.callback_query(F.data == CANCEL_CALLBACK)
    async def cancel(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        if callback.message is None:
            return
        if service.is_voice_note_active(callback.message.chat.id):
            await service.cancel_session(callback.message.chat.id)
        await state.clear()
        await callback.message.answer(
            service.build_cancel_message(),
            reply_markup=build_main_menu_keyboard(),
        )

    return router
