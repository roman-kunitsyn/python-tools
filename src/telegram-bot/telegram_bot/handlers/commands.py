from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from telegram_bot.keyboards.menu import build_main_menu_keyboard
from telegram_bot.keyboards.voice_note import build_voice_note_keyboard
from telegram_bot.services.voice_note import TelegramVoiceNoteService
from telegram_bot.states.voice_note import VoiceNoteStates


def build_command_router(service: TelegramVoiceNoteService) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message, state: FSMContext) -> None:
        if service.is_voice_note_active(message.chat.id):
            await message.answer(
                service.build_help_message(True),
                reply_markup=build_voice_note_keyboard(include_add_more=True),
            )
            return

        await state.clear()
        await message.answer(
            "Welcome.\n\n"
            "Use /voice_note to start a voice-note session, or /help for guidance.",
            reply_markup=build_main_menu_keyboard(),
        )

    @router.message(Command("help"))
    async def help_cmd(message: Message) -> None:
        await message.answer(
            service.build_help_message(service.is_voice_note_active(message.chat.id)),
            reply_markup=build_main_menu_keyboard(),
        )

    @router.message(Command("menu"))
    async def menu(message: Message, state: FSMContext) -> None:
        if not service.is_voice_note_active(message.chat.id):
            await state.clear()
        await message.answer(service.build_menu_message(), reply_markup=build_main_menu_keyboard())

    @router.message(Command("voice_note"))
    async def voice_note(message: Message, state: FSMContext) -> None:
        if service.is_voice_note_active(message.chat.id):
            await message.answer(
                "A voice note session is already active.",
                reply_markup=build_voice_note_keyboard(include_add_more=True),
            )
            return

        session = await service.start_session(message)
        await state.set_state(VoiceNoteStates.waiting_voice)
        await state.update_data(session_id=session.session_id)
        await message.answer(
            service.build_start_message(),
            reply_markup=build_voice_note_keyboard(include_add_more=False),
        )

    @router.message(Command("cancel"))
    async def cancel(message: Message, state: FSMContext) -> None:
        if service.is_voice_note_active(message.chat.id):
            await service.cancel_session(message.chat.id)
        await state.clear()
        await message.answer(
            service.build_cancel_message(),
            reply_markup=build_main_menu_keyboard(),
        )

    return router
