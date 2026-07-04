import math
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.timer import Timer
from textual.widgets import Footer, Header, Link, Static

from voice_note.models.session import VoiceNoteSession
from voice_note.models.settings import VoiceNoteSettings
from voice_note.services.runtime import build_service
from voice_note.services.session_service import SessionService
from voice_note.services.voice_note_service import VoiceNoteService
from voice_note.tui.screens import SessionChooserScreen, SessionChoice


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

    #session-link {
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
        ("enter", "open_session", "Open Session"),
        ("o", "open_session", "Open Session"),
        ("ctrl+s", "save_notes", "Save"),
        ("ctrl+l", "insert_timestamp", "Timestamp"),
        ("escape", "quit", "Exit"),
        ("ctrl+c", "quit", "Exit"),
    ]

    def __init__(
        self,
        settings: VoiceNoteSettings,
        session_service: SessionService,
    ) -> None:
        super().__init__()
        self.settings = settings
        self.session_service = session_service
        self.session: VoiceNoteSession | None = None
        self.service: VoiceNoteService | None = None
        self.recording = False
        self.notes: list[str] = []
        self.recording_started_at: float | None = None
        self.countdown_timer: Timer | None = None
        self.overflow_timer: Timer | None = None
        self.stopping = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Static("Choose or create a session", id="session-name"),
            SessionLink("Session: not selected", id="session-link"),
            Static("", id="notes"),
            id="content",
        )
        yield Container(
            Static("Status: Starting...", id="status", classes="status-idle"),
            Footer(),
            id="app-footer",
        )

    def on_mount(self) -> None:
        sessions = self.session_service.discover_sessions()
        self.push_screen(
            SessionChooserScreen(
                sessions=sessions,
                default_title=self.settings.session_title,
            ),
            callback=self._on_session_choice,
        )

    def _on_session_choice(self, choice: SessionChoice | None) -> None:
        if choice is None:
            self.exit()
            return

        self._activate_choice(choice)

    def _activate_choice(self, choice: SessionChoice) -> None:
        try:
            if choice.mode == "new":
                self.session = self.session_service.create_session(choice.title)
            elif choice.session_dir is not None:
                loaded = self.session_service.load_session(Path(choice.session_dir))
                if loaded is None:
                    raise RuntimeError(f"Unable to load session: {choice.session_dir}")
                self.session = loaded
            else:
                raise RuntimeError("No session was selected")
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            self.exit(1)
            return

        self.service = build_service(self.settings, self.session.session_dir)
        self._refresh_session_widgets()
        self._set_status("Status: Idle")

    def action_toggle_recording(self) -> None:
        if self.service is None:
            self._set_status("Status: Error: session is not ready")
            return

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

    def action_open_session(self) -> None:
        if self.session is None:
            self._set_status("Status: Error: session is not ready")
            return

        try:
            open_session_folder(self.session.session_dir, self.settings.editor, self)
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        self._set_status("Status: Saved")

    def action_insert_timestamp(self) -> None:
        from datetime import datetime

        self.notes.append(datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"))
        self._render_notes()

    def _stop_recording(self, time_overflow: bool = False) -> None:
        if self.service is None:
            self._set_status("Status: Error: session is not ready")
            return

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
            self.settings.max_recording_seconds,
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
            return self.settings.max_recording_seconds

        elapsed = time.monotonic() - self.recording_started_at
        return max(0, math.ceil(self.settings.max_recording_seconds - elapsed))

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

    def _refresh_session_widgets(self) -> None:
        if self.session is None:
            return

        self.query_one("#session-name", Static).update(self.session.title)
        self.query_one("#session-link", SessionLink).update(
            f"Session: {self.session.session_dir}"
        )
        self.query_one("#session-link", SessionLink).url = _transcript_url(
            self.session.session_dir,
            self.settings.editor,
        )

    @property
    def session_name(self) -> str:
        if self.session is None:
            return "Voice Note Session"
        return self.session.title

    @property
    def transcript_link(self) -> str:
        if self.session is None:
            return "Session: not selected"
        return f"Session: {self.session.session_dir}"

    @property
    def transcript_url(self) -> str | None:
        if self.session is None:
            return None
        return _transcript_url(self.session.session_dir, self.settings.editor)


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


def _session_name(target: VoiceNoteSession | Path | None) -> str:
    if target is None:
        return "Voice Note Session"

    if isinstance(target, VoiceNoteSession):
        return target.title

    if target.is_dir():
        return target.name

    return target.parent.name


def _transcript_link(target: VoiceNoteSession | Path | None) -> str:
    if target is None:
        return "Session: not selected"

    session_path = _session_path(target)
    if session_path is None:
        return "Session: not selected"

    return f"Session: {session_path}"


def _transcript_url(target: VoiceNoteSession | Path | None, editor: str = "code") -> str | None:
    if target is None:
        return None

    session_path = _session_path(target)
    if session_path is None:
        return None

    if _normalize_editor(editor) == "code":
        return _vscode_url(session_path)

    return session_path.resolve().as_uri()


def _session_path(target: VoiceNoteSession | Path) -> Path | None:
    if isinstance(target, VoiceNoteSession):
        return target.session_dir

    if target.is_dir():
        return target

    return target.parent


def open_session_folder(session_path: Path, editor: str, app: App) -> None:
    normalized_editor = _normalize_editor(editor)
    session_path.parent.mkdir(parents=True, exist_ok=True)
    session_path.mkdir(parents=True, exist_ok=True)

    if normalized_editor == "code":
        subprocess.run(_editor_command(session_path, normalized_editor), check=True)
        return

    with app.suspend():
        subprocess.run(_editor_command(session_path, normalized_editor), check=True)


def _normalize_editor(editor: str) -> str:
    normalized = editor.lower().strip()
    if normalized in {"code", "vscode", "vs-code"}:
        return "code"
    if normalized in {"nvim", "neovim"}:
        return "nvim"
    raise ValueError(f"Unsupported editor: {editor}")


def _vscode_url(target: Path) -> str:
    return f"vscode://file{quote(str(target.resolve()))}"


def _editor_command(target: Path, editor: str) -> list[str]:
    normalized_editor = _normalize_editor(editor)
    if normalized_editor == "code":
        return ["code", str(target)]

    return [normalized_editor, str(target)]


class SessionLink(Link):
    async def _on_click(self, event: events.Click) -> None:
        await super()._on_click(event)
        if event.widget is self:
            self.app.action_open_session()
            event.stop()

    def action_open_link(self) -> None:
        self.app.action_open_session()
