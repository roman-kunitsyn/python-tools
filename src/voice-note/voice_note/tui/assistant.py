from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Static

from voice_note.tui.views import AssistantMessageView


class AssistantTab(Vertical):
    def compose(self):
        yield Static("Assistant", id="assistant-title")
        yield Static(
            "Assistant messages are stored oldest to newest and use the current session as Ollama context.",
            id="assistant-card",
        )
        yield AssistantMessageView(id="assistant-messages")
        yield Static(
            "Use n to write a prompt, space to record one, p to play the selected prompt or response, and e/delete/y to edit, remove, or copy plain text.",
            id="assistant-details",
        )
        yield Static(
            "Navigate prompts and responses with j/k or the arrow keys. Use shift+j/k or shift+up/down to extend selection.",
            id="assistant-shortcuts",
        )


def build_assistant_tab() -> Vertical:
    return AssistantTab(id="assistant-view")
