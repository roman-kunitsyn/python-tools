from dataclasses import dataclass

from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static, TextArea

from voice_note.models.session import DEFAULT_SESSION_TITLE, VoiceNoteSession


@dataclass(frozen=True)
class SessionChoice:
    mode: str
    title: str | None = None
    session_dir: str | None = None


@dataclass(frozen=True)
class NoteEditResult:
    mode: str
    text: str | None = None


class SessionChooserScreen(ModalScreen[SessionChoice | None]):
    CSS = """
    SessionChooserScreen {
        align: center middle;
    }

    #dialog {
        width: 70;
        padding: 1 2;
        border: tall $accent;
        background: $surface;
    }

    #title {
        text-style: bold;
        margin-bottom: 1;
    }

    #actions {
        margin-top: 1;
        height: auto;
    }

    Select {
        width: 1fr;
    }

    Input {
        width: 1fr;
    }
    """

    def __init__(
        self,
        sessions: list[VoiceNoteSession],
        default_title: str = DEFAULT_SESSION_TITLE,
    ) -> None:
        super().__init__()
        self.sessions = sessions
        self.default_title = default_title
        self._selected_session_dir: str | None = None

    def compose(self):
        yield Container(
            Static("Voice Note Session", id="title"),
            Static(
                "Create a new session or continue an existing one.",
                classes="subtitle",
            ),
            Vertical(
                Label("New session title"),
                Input(value=self.default_title, id="session-title"),
                Label("Existing sessions"),
                Select(
                    self._session_options(),
                    prompt="Choose a session",
                    allow_blank=True,
                    id="existing-session",
                ),
                id="form",
            ),
            Container(
                Button("Start New", variant="primary", id="start-new"),
                Button("Continue", id="continue-existing"),
                Button("Cancel", variant="error", id="cancel-session"),
                id="actions",
            ),
            id="dialog",
        )

    def on_mount(self) -> None:
        self.query_one("#session-title", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "session-title":
            self._start_new_session()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "existing-session":
            value = event.value
            self._selected_session_dir = None if value is Select.BLANK else str(value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "start-new":
            self._start_new_session()
        elif button_id == "continue-existing":
            self._continue_existing_session()
        elif button_id == "cancel-session":
            self.dismiss(None)

    def _start_new_session(self) -> None:
        title = self.query_one("#session-title", Input).value.strip()
        self.dismiss(SessionChoice(mode="new", title=title or DEFAULT_SESSION_TITLE))

    def _continue_existing_session(self) -> None:
        if self._selected_session_dir is None:
            return

        session = next(
            (item for item in self.sessions if str(item.session_dir) == self._selected_session_dir),
            None,
        )
        if session is not None:
            self.dismiss(
                SessionChoice(
                    mode="existing",
                    session_dir=str(session.session_dir),
                )
            )

    def _session_options(self) -> list[tuple[str, str]]:
        if not self.sessions:
            return [("No existing sessions", "")]

        return [
            (f"{session.title}  ({session.timestamp})", str(session.session_dir))
            for session in self.sessions
        ]


class NoteEditorScreen(ModalScreen[NoteEditResult | None]):
    BINDINGS = [
        ("ctrl+enter", "submit", "Save"),
        ("escape", "cancel", "Cancel"),
    ]

    CSS = """
    NoteEditorScreen {
        align: center middle;
    }

    #dialog {
        width: 80;
        height: 24;
        padding: 1 2;
        border: tall $accent;
        background: $surface;
    }

    #title {
        text-style: bold;
        margin-bottom: 1;
    }

    #editor {
        height: 1fr;
        border: solid $surface;
        margin: 1 0;
    }

    #actions {
        height: auto;
        layout: horizontal;
        margin-top: 1;
    }
    """

    def __init__(self, title: str, text: str = "") -> None:
        super().__init__()
        self.title = title
        self.text = text

    def compose(self):
        yield Container(
            Static(self.title, id="title"),
            Static("Ctrl+Enter saves, Esc cancels."),
            TextArea(text=self.text, id="editor"),
            Container(
                Button("Save [Ctrl+Enter]", variant="primary", id="save-note"),
                Button("Cancel [Esc]", variant="error", id="cancel-note"),
                id="actions",
            ),
            id="dialog",
        )

    def on_mount(self) -> None:
        self.query_one("#editor", TextArea).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-note":
            self.action_submit()
        elif event.button.id == "cancel-note":
            self.action_cancel()

    def action_submit(self) -> None:
        self.dismiss(
            NoteEditResult(
                mode="save",
                text=self.query_one("#editor", TextArea).text,
            )
        )

    def action_cancel(self) -> None:
        self.dismiss(NoteEditResult(mode="cancel"))
