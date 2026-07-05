from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Static

from voice_note.tui.views import AssistantMessageView


class AssistantTab(Vertical):
    def compose(self):
        yield Static("Assistant", id="assistant-title")
        yield Static(
            "Prompt Ollama with session context and review generated replies.",
            id="assistant-card",
        )
        yield AssistantMessageView(id="assistant-messages")
        yield Static(
            "Use n to write a prompt, space to record one, and j/k or arrows to move through prompts and replies.",
            id="assistant-details",
        )


def build_assistant_tab() -> Vertical:
    return AssistantTab(id="assistant-view")
