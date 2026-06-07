from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button


class ActionButtons(Horizontal):
    def compose(self) -> ComposeResult:
        yield Button("Start", variant="primary", id="start")
        yield Button("Cancel", id="cancel")
