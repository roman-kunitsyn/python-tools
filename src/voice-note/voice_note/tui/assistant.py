from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Button, Input, Static

from voice_note.tui.views import AssistantMessageView


class AssistantTab(Vertical):
    def compose(self):
        yield Static("Assistant", id="assistant-title")
        yield Static(
            "Prompt Ollama with session context and review generated replies.",
            id="assistant-card",
        )
        yield AssistantMessageView(id="assistant-messages")
        yield Input(
            placeholder="Ask Ollama about this session...",
            id="assistant-prompt",
        )
        yield Button("Send", variant="primary", id="assistant-send")
        yield Static(
            "The session QR and assistant link remain available from the Session tab.",
            id="assistant-details",
        )


def build_assistant_tab() -> Vertical:
    return AssistantTab(id="assistant-view")
