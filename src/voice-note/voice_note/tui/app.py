import math
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

from textual.app import App, ComposeResult
from textual.containers import Container
from textual import events
from textual.timer import Timer
from textual.widgets import Footer, Header, Link, Static

from voice_note.services.voice_note_service import VoiceNoteService


STATUS_CLASSES = (
    "status-idle",
    "status-recording",
    "status-transcribing",
    "status-saved",
    "status-overflow",
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

    #status.status-overflow {
        background: $warning;
        color: black;
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

    def __init__(
        self,
        service: VoiceNoteService,
        editor: str = "code",
        max_recording_seconds: int = 300,
    ) -> None:
        super().__init__()
        self.service = service
        self.editor = editor
        self.max_recording_seconds = max_recording_seconds
        self.recording = False
        self.notes: list[str] = []
        self.recording_started_at: float | None = None
        self.countdown_timer: Timer | None = None
        self.overflow_timer: Timer | None = None
        self.stopping = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static(self.session_name, id="session-name"),
            TranscriptLink(
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
        self.stopping = False
        self.recording_started_at = time.monotonic()
        self._start_countdown_timers()
        self._set_recording_status()

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

    def _stop_recording(self, time_overflow: bool = False) -> None:
        if self.stopping:
            return

        self.stopping = True
        self.recording = False
        self._stop_countdown_timers()

        if time_overflow:
            self._set_status("Status: Record Stop by time overflow")
        else:
            self._set_status("Status: Transcribing...")

        def work() -> None:
            try:
                note = self.service.stop_recording_and_transcribe()
            except Exception as error:
                self.call_from_thread(self._set_status, f"Status: Error: {error}")
                return

            self.call_from_thread(self._add_note, note.text)

        self.run_worker(work, thread=True)

    def _start_countdown_timers(self) -> None:
        self._stop_countdown_timers()
        self.countdown_timer = self.set_interval(1, self._set_recording_status)
        self.overflow_timer = self.set_timer(
            self.max_recording_seconds,
            self._handle_time_overflow,
        )

    def _stop_countdown_timers(self) -> None:
        for timer in (self.countdown_timer, self.overflow_timer):
            if timer is not None:
                timer.stop()
        self.countdown_timer = None
        self.overflow_timer = None

    def _handle_time_overflow(self) -> None:
        if self.recording:
            self._stop_recording(time_overflow=True)

    def _set_recording_status(self) -> None:
        self._set_status(
            f"Status: Recording... {_format_countdown(self._remaining_seconds())}"
        )

    def _remaining_seconds(self) -> int:
        if self.recording_started_at is None:
            return self.max_recording_seconds

        elapsed = time.monotonic() - self.recording_started_at
        return max(0, math.ceil(self.max_recording_seconds - elapsed))

    def _add_note(self, text: str) -> None:
        self.notes.append(text)
        self._render_notes()
        self.recording_started_at = None
        self.stopping = False
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

    if "overflow" in normalized:
        return "status-overflow"

    if "error" in normalized:
        return "status-error"

    return "status-idle"


def _format_countdown(seconds: int) -> str:
    minutes, remaining_seconds = divmod(max(0, seconds), 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"


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
        subprocess.run(_editor_command(transcript_file, normalized_editor), check=True)
        return

    with app.suspend():
        subprocess.run(_editor_command(transcript_file, normalized_editor), check=True)


def _normalize_editor(editor: str) -> str:
    normalized = editor.lower().strip()
    if normalized in {"code", "vscode", "vs-code"}:
        return "code"
    if normalized in {"nvim", "neovim"}:
        return "nvim"
    raise ValueError(f"Unsupported editor: {editor}")


def _vscode_url(transcript_file: Path) -> str:
    return f"vscode://file{quote(str(transcript_file.resolve()))}"


def _editor_command(transcript_file: Path, editor: str) -> list[str]:
    normalized_editor = _normalize_editor(editor)
    if normalized_editor == "code":
        return ["code", "-g", str(transcript_file)]

    return [normalized_editor, str(transcript_file)]


class TranscriptLink(Link):
    async def _on_click(self, event: events.Click) -> None:
        await super()._on_click(event)
        if event.widget is self:
            self.app.action_open_transcript()
            event.stop()

    def action_open_link(self) -> None:
        self.app.action_open_transcript()
