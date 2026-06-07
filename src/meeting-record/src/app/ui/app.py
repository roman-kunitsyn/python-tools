from textual.app import App

from src.app.models.config import RecordConfig
from src.app.ui.screens.record_screen import RecordScreen


class MeetingRecordApp(App):
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

    Input {
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
        min-height: 4;
    }
    """

    BINDINGS = [
        ("escape", "quit", "Cancel"),
    ]

    def __init__(self, config: RecordConfig) -> None:
        super().__init__()
        self.config = config

    def on_mount(self) -> None:
        self.push_screen(RecordScreen())
