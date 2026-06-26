from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


START_VOICE_NOTE_CALLBACK = "menu:voice_note"
HELP_CALLBACK = "menu:help"


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎤 Voice Note",
                    callback_data=START_VOICE_NOTE_CALLBACK,
                ),
                InlineKeyboardButton(
                    text="❓ Help",
                    callback_data=HELP_CALLBACK,
                ),
            ]
        ]
    )
