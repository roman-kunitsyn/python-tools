from textual.app import App

from src.app.models.config import TranscribeConfig
from src.app.ui.screens.transcribe_screen import TranscribeScreen


class TranscribeApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #content {
        padding: 1 2;
    }

    .form-field {
        margin-bottom: 1;
    }

    Label {
        margin-bottom: 1;
    }

    Input, Select {
        width: 100%;
    }

    #actions {
        height: auto;
        margin-top: 1;
    }

    #actions Button {
        margin-right: 1;
    }

    #status {
        margin-top: 1;
        min-height: 3;
    }
    """

    BINDINGS = [
        ("escape", "quit", "Cancel"),
    ]

    def __init__(self, config: TranscribeConfig) -> None:
        super().__init__()
        self.config = config

    def on_mount(self) -> None:
        self.push_screen(TranscribeScreen())
