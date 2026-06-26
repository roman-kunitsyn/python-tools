from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


ADD_MORE_CALLBACK = "voice_note:add_more"
FINISH_CALLBACK = "voice_note:finish"
CANCEL_CALLBACK = "voice_note:cancel"


def build_voice_note_keyboard(include_add_more: bool = True) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if include_add_more:
        rows.append(
            [InlineKeyboardButton(text="➕ Add More", callback_data=ADD_MORE_CALLBACK)]
        )

    rows.append(
        [
            InlineKeyboardButton(text="✅ Finish", callback_data=FINISH_CALLBACK),
            InlineKeyboardButton(text="❌ Cancel", callback_data=CANCEL_CALLBACK),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
