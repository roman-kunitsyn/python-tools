from __future__ import annotations

from textual.containers import Vertical
from textual.widgets import Static


class AssistantTab(Vertical):
    def compose(self):
        yield Static("Assistant", id="assistant-title")
        yield Static(
            "Use this tab for session assistance and future assistant workflows.",
            id="assistant-card",
        )
        yield Static(
            "The session QR and assistant link remain available from the Session tab.",
            id="assistant-details",
        )


def build_assistant_tab() -> Vertical:
    return AssistantTab(id="assistant-view")
