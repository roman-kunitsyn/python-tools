from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class VoiceNoteStates(StatesGroup):
    waiting_voice = State()
    waiting_decision = State()
