import subprocess
from pathlib import Path
from urllib.parse import quote

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Link, Static

from voice_note.services.voice_note_service import VoiceNoteService


STATUS_CLASSES = (
    "status-idle",
    "status-recording",
    "status-transcribing",
    "status-saved",
    "status-error",
)


class VoiceNoteApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #content {
        height: 1fr;
        padding: 1 2;
    }

    #notes {
        min-height: 12;
        border: solid $surface;
        padding: 1;
    }

    #session-name {
        text-style: bold;
    }

    #transcript-link {
        color: $accent;
    }

    #app-footer {
        height: auto;
        dock: bottom;
    }

    #status {
        height: 1;
        padding: 0 1;
        color: white;
        text-style: bold;
    }

    #status.status-idle {
        background: $surface;
    }

    #status.status-recording {
        background: $error;
    }

    #status.status-transcribing {
        background: $warning;
        color: black;
    }

    #status.status-saved {
        background: $success;
    }

    #status.status-error {
        background: $error;
    }
    """

    BINDINGS = [
        ("space", "toggle_recording", "Record"),
        ("o", "open_transcript", "Open Transcript"),
        ("ctrl+s", "save_notes", "Save"),
        ("ctrl+l", "insert_timestamp", "Timestamp"),
        ("escape", "quit", "Exit"),
        ("ctrl+c", "quit", "Exit"),
    ]

    def __init__(self, service: VoiceNoteService, editor: str = "code") -> None:
        super().__init__()
        self.service = service
        self.editor = editor
        self.recording = False
        self.notes: list[str] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static(self.session_name, id="session-name"),
            Link(
                self.transcript_link,
                url=self.transcript_url,
                id="transcript-link",
            ),
            Static("", id="notes"),
            id="content",
        )
        yield Container(
            Static("Status: Idle", id="status", classes="status-idle"),
            Footer(),
            id="app-footer",
        )

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

    def action_open_transcript(self) -> None:
        transcript_file = self.service.output_file
        if transcript_file is None:
            self._set_status("Status: Error: transcript is stdout")
            return

        try:
            open_transcript_file(transcript_file, self.editor, self)
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

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
        status_widget = self.query_one("#status", Static)
        status_widget.update(_format_status(status))

        for status_class in STATUS_CLASSES:
            status_widget.remove_class(status_class)
        status_widget.add_class(_status_class(status))

    @property
    def session_name(self) -> str:
        return _session_name(self.service.output_file)

    @property
    def transcript_link(self) -> str:
        return _transcript_link(self.service.output_file)

    @property
    def transcript_url(self) -> str | None:
        return _transcript_url(self.service.output_file, self.editor)


def _format_status(status: str) -> str:
    if status.startswith("Status:"):
        return status
    return f"Status: {status}"


def _status_class(status: str) -> str:
    normalized = status.lower()

    if "recording" in normalized:
        return "status-recording"

    if "transcrib" in normalized:
        return "status-transcribing"

    if "saved" in normalized:
        return "status-saved"

    if "error" in normalized:
        return "status-error"

    return "status-idle"


def _session_name(transcript_file) -> str:
    if transcript_file is None:
        return "Voice Note Session"

    return transcript_file.parent.name


def _transcript_link(transcript_file) -> str:
    if transcript_file is None:
        return "Transcript: stdout"

    return f"Transcript: {transcript_file}"


def _transcript_url(transcript_file, editor: str = "code") -> str | None:
    if transcript_file is None:
        return None

    if _normalize_editor(editor) == "code":
        return _vscode_url(transcript_file)

    return transcript_file.resolve().as_uri()


def open_transcript_file(transcript_file: Path, editor: str, app: App) -> None:
    normalized_editor = _normalize_editor(editor)
    transcript_file.parent.mkdir(parents=True, exist_ok=True)
    transcript_file.touch(exist_ok=True)

    if normalized_editor == "code":
        app.open_url(_vscode_url(transcript_file))
        return

    with app.suspend():
        subprocess.run([normalized_editor, str(transcript_file)], check=True)


def _normalize_editor(editor: str) -> str:
    normalized = editor.lower().strip()
    if normalized in {"code", "vscode", "vs-code"}:
        return "code"
    if normalized in {"nvim", "neovim"}:
        return "nvim"
    raise ValueError(f"Unsupported editor: {editor}")


def _vscode_url(transcript_file: Path) -> str:
    return f"vscode://file{quote(str(transcript_file.resolve()))}"
