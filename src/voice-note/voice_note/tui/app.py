from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from voice_note.services.voice_note_service import VoiceNoteService


class VoiceNoteApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #content {
        padding: 1 2;
    }

    #notes {
        min-height: 12;
        border: solid $surface;
        padding: 1;
    }

    #status {
        height: 3;
        padding: 1 0;
    }
    """

    BINDINGS = [
        ("space", "toggle_recording", "Record"),
        ("ctrl+s", "save_notes", "Save"),
        ("ctrl+l", "insert_timestamp", "Timestamp"),
        ("escape", "quit", "Exit"),
        ("ctrl+c", "quit", "Exit"),
    ]

    def __init__(self, service: VoiceNoteService) -> None:
        super().__init__()
        self.service = service
        self.recording = False
        self.notes: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Previous Notes", id="title"),
            Static("", id="notes"),
            Static("Status: Idle", id="status"),
            id="content",
        )
        yield Footer()

    def action_toggle_recording(self) -> None:
        if self.recording:
            self._stop_recording()
            return

        try:
            self.service.start_recording()
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        self.recording = True
        self._set_status("Status: Recording...")

    def action_save_notes(self) -> None:
        self._set_status("Status: Saved")

    def action_insert_timestamp(self) -> None:
        from datetime import datetime

        self.notes.append(datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"))
        self._render_notes()

    def _stop_recording(self) -> None:
        self.recording = False
        self._set_status("Status: Transcribing...")

        def work() -> None:
            try:
                note = self.service.stop_recording_and_transcribe()
            except Exception as error:
                self.call_from_thread(self._set_status, f"Status: Error: {error}")
                return

            self.call_from_thread(self._add_note, note.text)

        self.run_worker(work, thread=True)

    def _add_note(self, text: str) -> None:
        self.notes.append(text)
        self._render_notes()
        self._set_status("Status: Idle")

    def _render_notes(self) -> None:
        body = "\n\n".join(f"- {note}" for note in self.notes)
        self.query_one("#notes", Static).update(body)

    def _set_status(self, status: str) -> None:
        self.query_one("#status", Static).update(status)
