import math
import hashlib
import subprocess
import time
from pathlib import Path
from urllib.parse import quote

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.timer import Timer
from textual.widgets import (
    Button,
    Footer,
    Header,
    Link,
    Static,
    TabbedContent,
    TabPane,
)

from voice_note.audio.player import play_audio_file, speak_text
from voice_note.models.assistant_message import AssistantMessage
from voice_note.models.session import VoiceNoteSession
from voice_note.models.session_note import SessionNote
from voice_note.models.settings import VoiceNoteSettings
from voice_note.output.assistant_store import AssistantMessageStore
from voice_note.services.runtime import build_service
from voice_note.services.assistant_service import AssistantService
from voice_note.services.ollama_client import OllamaClient
from voice_note.services.session_service import SessionService
from voice_note.services.voice_note_service import VoiceNoteService
from voice_note.tui.clipboard import copy_text_to_clipboard
from voice_note.tui.assistant import build_assistant_tab
from voice_note.tui.views import AssistantMessageView, NoteTranscriptView
from voice_note.tui.screens import (
    NoteEditResult,
    NoteEditorScreen,
    SessionChooserScreen,
    SessionChoice,
)


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

    Screen.recording {
        background: $error;
    }

    Screen.recording #status {
        text-style: bold blink;
    }

    #workspace {
        height: 1fr;
        padding: 1 2;
        layout: vertical;
    }

    #main-tabs {
        height: 1fr;
    }

    TabPane {
        height: 1fr;
    }

    #notes {
        height: 1fr;
    }

    #summary-bar {
        height: auto;
        layout: horizontal;
    }

    #session-card,
    #qr-card,
    #details-card,
    #notes-panel {
        border: solid $surface;
        padding: 1;
    }

    #session-card {
        width: 1fr;
        height: auto;
    }

    #qr-card {
        width: 1fr;
        height: auto;
        margin-left: 1;
    }

    #session-title {
        text-style: bold;
    }

    #session-description {
        color: $text-muted;
    }

    #session-folder-path {
        color: $accent;
        text-style: underline;
    }

    #main-panels {
        height: 1fr;
        layout: vertical;
        margin-top: 1;
    }

    #notes-panel {
        height: 1fr;
        layout: vertical;
    }

    #notes-content {
        height: 1fr;
        width: 1fr;
    }

    #details-card {
        height: auto;
        layout: vertical;
        margin-top: 1;
    }

    #note-detail {
        height: auto;
    }

    #note-actions {
        height: auto;
    }

    #qr-code {
        color: $accent;
        padding: 1;
        height: auto;
    }

    #zoom-controls {
        height: auto;
        layout: horizontal;
        margin-left: 1;
    }

    #note-actions {
        height: auto;
        layout: horizontal;
        margin-top: 1;
    }

    #help-card,
    #settings-card {
        border: solid $surface;
        padding: 1;
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

    #status.status-recording-alt {
        background: $warning;
        color: black;
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
        ("n", "new_note", "New Note"),
        ("e", "edit_note", "Edit Note"),
        ("delete", "delete_note", "Delete Note"),
        ("p", "play_note", "Play Note"),
        ("j", "next_note", "Next Note"),
        ("k", "previous_note", "Previous Note"),
        ("down", "next_note", "Next Note"),
        ("up", "previous_note", "Previous Note"),
        ("shift+j", "extend_next_note", "Extend Selection"),
        ("shift+k", "extend_previous_note", "Extend Selection"),
        ("shift+down", "extend_next_note", "Extend Selection"),
        ("shift+up", "extend_previous_note", "Extend Selection"),
        ("y", "copy_selection", "Copy Selection"),
        ("ctrl+shift+c", "copy_selection", "Copy Selection"),
        ("+", "zoom_in", "Zoom In"),
        ("-", "zoom_out", "Zoom Out"),
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
        self.assistant_store: AssistantMessageStore | None = None
        self.assistant_service: AssistantService | None = None
        self.assistant_messages: list[AssistantMessage] = []
        self.active_tab = "notes"
        self.recording_mode = "notes"
        self.recording = False
        self.notes: list[SessionNote] = []
        self.selected_note_id: str | None = None
        self.selection_anchor_index: int | None = None
        self.selection_end_index: int | None = None
        self.assistant_selected_message_id: str | None = None
        self.assistant_selection_anchor_index: int | None = None
        self.assistant_selection_end_index: int | None = None
        self.recording_started_at: float | None = None
        self.countdown_timer: Timer | None = None
        self.status_blink_timer: Timer | None = None
        self.overflow_timer: Timer | None = None
        self.stopping = False
        self.note_zoom = 1
        self._status_blink_state = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="workspace"):
            with TabbedContent(initial="notes", id="main-tabs"):
                with TabPane("Notes", id="notes"):
                    yield Vertical(
                        NoteTranscriptView(id="notes-content"),
                        id="notes-panel",
                    )
                with TabPane("Assistant", id="assistant"):
                    yield build_assistant_tab()
                with TabPane("Session", id="session"):
                    yield Vertical(
                        Horizontal(
                            Vertical(
                                Static("", id="session-title"),
                                Static("", id="session-description"),
                                SessionLink(
                                    "Session: not selected", id="session-folder-path"
                                ),
                                Button(
                                    "Open Folder",
                                    variant="primary",
                                    id="open-session-session",
                                ),
                                id="session-card",
                            ),
                            Vertical(
                                Static("Telegram assistant", id="qr-title"),
                                Static("", id="qr-code"),
                                id="qr-card",
                            ),
                            id="summary-bar",
                        ),
                    )
                with TabPane("Help", id="help"):
                    yield Vertical(
                        Static("About", id="help-title"),
                        Static(
                            "Voice Note is a push-to-talk TUI for recording, transcribing, and editing human-readable session artefacts.",
                            id="help-card",
                        ),
                        Static(
                            "Use Notes for transcripts, Session for folder and QR access, and Settings for source/output configuration.",
                            id="help-details",
                        ),
                        id="help-view",
                    )
                with TabPane("Settings", id="settings"):
                    yield Vertical(
                        Static("Settings", id="settings-title"),
                        Static("", id="settings-inputs"),
                        Static("", id="settings-outputs"),
                        Static("", id="settings-runtime"),
                        id="settings-view",
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
        if self.service.session_store is not None:
            self.notes = self.service.session_store.load_notes()
        self.assistant_store = AssistantMessageStore(
            messages_file=self.session.assistant_file,
            transcript_file=self.session.assistant_transcript_file,
            session=self.session.session_dir.name,
        )
        self.assistant_service = AssistantService(
            session=self.session,
            notes_store=self.service.session_store,
            assistant_store=self.assistant_store,
            ollama_client=OllamaClient(model=self.settings.model),
        )
        self._reload_assistant_messages()
        self._refresh_session_widgets()
        self._refresh_settings_widgets()
        self._render_notes()
        self._render_assistant_messages()
        self._set_status("Status: Idle")
        self._show_tab("notes")

    def action_toggle_recording(self) -> None:
        if self.service is None:
            self._set_status("Status: Error: session is not ready")
            return

        if self.recording:
            self._stop_recording()
            return

        self.recording_mode = self._workspace_tab()

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
        self._set_recording_theme(True)

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
        self.action_new_note()

    def action_new_note(self) -> None:
        if self._workspace_tab() == "assistant":
            self._open_assistant_prompt_editor(title="New prompt")
            return
        self._open_note_editor(title="New note")

    def action_edit_note(self) -> None:
        if self._workspace_tab() == "assistant":
            self.action_edit_assistant_message()
            return
        note = self._selected_note()
        if note is None:
            self._set_status("Status: Error: no note selected")
            return

        self._open_note_editor(title="Edit note", note=note)

    def action_delete_note(self) -> None:
        if self._workspace_tab() == "assistant":
            self.action_delete_assistant_message()
            return
        note = self._selected_note()
        if note is None:
            self._set_status("Status: Error: no note selected")
            return

        if self.service is None or self.service.session_store is None:
            self._set_status("Status: Error: session store is not ready")
            return

        try:
            self.service.session_store.delete_note(note.note_id)
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        self._reload_notes_from_store()
        self._set_status("Status: Saved")

    def action_play_note(self) -> None:
        if self._workspace_tab() == "assistant":
            self.action_play_assistant_message()
            return
        note = self._selected_note()
        if note is None:
            self._set_status("Status: Error: no note selected")
            return

        self._set_status("Status: Playing...")

        def work() -> None:
            try:
                if note.audio_file is not None:
                    play_audio_file(note.audio_file)
                else:
                    speak_text(note.text)
            except Exception as error:
                self.call_from_thread(self._set_status, f"Status: Error: {error}")
                return

            self.call_from_thread(self._set_status, "Status: Saved")

        self.run_worker(work, thread=True)

    def action_zoom_in(self) -> None:
        self._set_note_zoom(min(3, self.note_zoom + 1))

    def action_zoom_out(self) -> None:
        self._set_note_zoom(max(1, self.note_zoom - 1))

    def action_show_notes_tab(self) -> None:
        self._show_tab("notes")

    def action_show_session_tab(self) -> None:
        self._show_tab("session")

    def action_show_help_tab(self) -> None:
        self._show_tab("help")

    def action_show_assistant_tab(self) -> None:
        self._show_tab("assistant")

    def action_show_settings_tab(self) -> None:
        self._show_tab("settings")

    def action_next_note(self) -> None:
        if self._workspace_tab() == "assistant":
            self._move_assistant_message_selection(1)
            return
        self._move_note_selection(1)

    def action_previous_note(self) -> None:
        if self._workspace_tab() == "assistant":
            self._move_assistant_message_selection(-1)
            return
        self._move_note_selection(-1)

    def action_extend_next_note(self) -> None:
        if self._workspace_tab() == "assistant":
            self._move_assistant_message_selection(1, extend_selection=True)
            return
        self._move_note_selection(1, extend_selection=True)

    def action_extend_previous_note(self) -> None:
        if self._workspace_tab() == "assistant":
            self._move_assistant_message_selection(-1, extend_selection=True)
            return
        self._move_note_selection(-1, extend_selection=True)

    def action_copy_selection(self) -> None:
        if self._workspace_tab() == "assistant":
            text = self._selected_assistant_messages_text()
            if text == "":
                self._set_status("Status: Error: no assistant text to copy")
                return

            try:
                copy_text_to_clipboard(text)
            except Exception as error:
                self._set_status(f"Status: Error: {error}")
                return

            self._set_status("Status: Copied")
            return

        text = self._selected_notes_text()
        if text == "":
            self._set_status("Status: Error: no note text to copy")
            return

        try:
            copy_text_to_clipboard(text)
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        self._set_status("Status: Copied")

    def action_send_assistant_prompt(self, prompt: str | None = None) -> None:
        if self.assistant_service is None:
            self._set_status("Status: Error: assistant is not ready")
            return

        text = (prompt or "").strip()
        if text == "":
            self._set_status("Status: Error: no assistant prompt")
            return

        self._submit_assistant_prompt(text)

    def action_play_assistant_message(self) -> None:
        message = self._selected_assistant_message()
        if message is None:
            self._set_status("Status: Error: no assistant message selected")
            return

        self._set_status("Status: Playing...")

        def work() -> None:
            try:
                if message.role == "user" and message.source_audio is not None:
                    play_audio_file(message.source_audio)
                    return

                text = message.response if message.role != "user" else message.prompt
                if text.strip() == "":
                    raise RuntimeError("assistant message has no text to play")
                speak_text(text)
            except Exception as error:
                self.call_from_thread(self._set_status, f"Status: Error: {error}")
                return

            self.call_from_thread(self._set_status, "Status: Saved")

        self.run_worker(work, thread=True)

    def action_edit_assistant_message(self) -> None:
        message = self._selected_assistant_message()
        if message is None:
            self._set_status("Status: Error: no assistant message selected")
            return

        initial_text = message.prompt if message.role == "user" else message.response
        self.push_screen(
            NoteEditorScreen(title="Edit assistant message", text=initial_text),
            callback=lambda result: self._on_assistant_editor_result(result, message),
        )

    def _open_assistant_prompt_editor(self, title: str) -> None:
        self.push_screen(
            NoteEditorScreen(title=title, text=""),
            callback=self._on_assistant_prompt_editor_result,
        )

    def action_delete_assistant_message(self) -> None:
        message = self._selected_assistant_message()
        if message is None:
            self._set_status("Status: Error: no assistant message selected")
            return

        if self.assistant_store is None:
            self._set_status("Status: Error: assistant store is not ready")
            return

        try:
            self.assistant_store.delete_message(message.message_id)
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        self._reload_assistant_messages()
        self._set_status("Status: Saved")

    def _stop_recording(self, time_overflow: bool = False) -> None:
        if self.service is None:
            self._set_status("Status: Error: session is not ready")
            return

        if self.stopping:
            return

        self.stopping = True
        self.recording = False
        self._stop_countdown_timers()
        self._set_recording_theme(False)

        if time_overflow:
            self._set_status("Status: Record Stop by time overflow")
        else:
            self._set_status("Status: Transcribing...")

        assistant_mode = self.recording_mode == "assistant"

        def work() -> None:
            try:
                if assistant_mode:
                    note = self.service.stop_recording_and_transcribe(persist=False)
                else:
                    note = self.service.stop_recording_and_transcribe()
            except Exception as error:
                self.call_from_thread(self._set_status, f"Status: Error: {error}")
                return

            if assistant_mode:
                self.recording_started_at = None
                self.stopping = False
                if self.assistant_service is None:
                    self.call_from_thread(self._set_status, "Status: Error: assistant is not ready")
                    return

                self.call_from_thread(
                    self._submit_assistant_prompt,
                    note.text,
                    note.audio_file,
                )
                return

            self.call_from_thread(self._add_note, note.text)

        self.run_worker(work, thread=True)

    def _start_countdown_timers(self) -> None:
        self._stop_countdown_timers()
        self.countdown_timer = self.set_interval(1, self._set_recording_status)
        self.status_blink_timer = self.set_interval(0.5, self._toggle_status_blink)
        self.overflow_timer = self.set_timer(
            self.settings.max_recording_seconds,
            self._handle_time_overflow,
        )

    def _stop_countdown_timers(self) -> None:
        for timer in (
            self.countdown_timer,
            self.status_blink_timer,
            self.overflow_timer,
        ):
            if timer is not None:
                timer.stop()
        self.countdown_timer = None
        self.status_blink_timer = None
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
        if self.service is None or self.service.session_store is None:
            return

        self.recording_mode = "notes"
        self.notes = self.service.session_store.load_notes()
        if self.notes:
            self.selected_note_id = self.notes[-1].note_id
            self.selection_anchor_index = len(self.notes) - 1
            self.selection_end_index = len(self.notes) - 1
        self._render_notes()
        self.recording_started_at = None
        self.stopping = False
        self._set_status("Status: Idle")

    def _render_notes(self) -> None:
        if self.notes:
            if self.selected_note_id is None or self.selected_note_id not in {
                note.note_id for note in self.notes
            }:
                self.selected_note_id = self.notes[0].note_id
                self.selection_anchor_index = 0
                self.selection_end_index = 0

        notes_view = self.query_one("#notes-content", NoteTranscriptView)
        selection_bounds = self._selected_note_bounds()
        notes_view.render_notes(
            self.notes,
            selected_note_id=self.selected_note_id,
            selected_note_bounds=selection_bounds,
            zoom=self.note_zoom,
        )
        if self.session is not None:
            self.query_one("#session-description", Static).update(
                f"{self.session.slug} • {self.session.timestamp} • {len(self.notes)} notes"
            )

    def _reload_assistant_messages(
        self, select_message_id: str | None = None
    ) -> None:
        if self.assistant_store is None:
            return

        self.assistant_messages = self.assistant_store.load_messages()
        if not self.assistant_messages:
            self.assistant_selected_message_id = None
            self.assistant_selection_anchor_index = None
            self.assistant_selection_end_index = None
        elif select_message_id is not None and select_message_id in {
            message.message_id for message in self.assistant_messages
        }:
            self.assistant_selected_message_id = select_message_id
            index = self._assistant_selected_message_index()
            self.assistant_selection_anchor_index = index
            self.assistant_selection_end_index = index
        elif self.assistant_selected_message_id is None or self.assistant_selected_message_id not in {
            message.message_id for message in self.assistant_messages
        }:
            self.assistant_selected_message_id = self.assistant_messages[-1].message_id
            index = len(self.assistant_messages) - 1
            self.assistant_selection_anchor_index = index
            self.assistant_selection_end_index = index
        self._render_assistant_messages()

    def _render_assistant_messages(self) -> None:
        try:
            messages_view = self.query_one("#assistant-messages", AssistantMessageView)
        except Exception:
            return

        selection_bounds = self._selected_assistant_message_bounds()
        messages_view.render_messages(
            self.assistant_messages,
            selected_message_id=self.assistant_selected_message_id,
            selected_message_bounds=selection_bounds,
        )

    def _submit_assistant_prompt(
        self,
        prompt: str,
        source_audio: Path | None = None,
    ) -> None:
        if self.assistant_service is None or self.assistant_store is None:
            self._set_status("Status: Error: assistant is not ready")
            return

        prompt = prompt.strip()
        if prompt == "":
            self._set_status("Status: Error: no assistant prompt")
            return

        self.recording_mode = "assistant"
        self.recording_started_at = None
        self.stopping = False

        prompt_message = self.assistant_store.append_message(
            role="user",
            prompt=prompt,
            response="",
            response_state="sent",
            source_audio=source_audio,
        )
        self._reload_assistant_messages(select_message_id=prompt_message.message_id)
        self._set_status("Status: Generating assistant response...")

        def work() -> None:
            try:
                response_text = self.assistant_service.generate_response_text(prompt)
            except Exception as error:
                try:
                    error_message = self.assistant_store.append_message(
                        role="assistant",
                        prompt=prompt,
                        response=f"Error: {error}",
                        response_state="error",
                        source_audio=source_audio,
                    )
                    self.call_from_thread(
                        self._reload_assistant_messages,
                        error_message.message_id,
                    )
                except Exception as store_error:
                    self.call_from_thread(
                        self._set_status,
                        f"Status: Error: {store_error}",
                    )
                    return
                self.call_from_thread(self._set_status, f"Status: Error: {error}")
                self.call_from_thread(self._reset_assistant_recording_state, None)
                return

            try:
                response_message = self.assistant_store.append_message(
                    role="assistant",
                    prompt=prompt,
                    response=response_text,
                    response_state="complete",
                    source_audio=source_audio,
                )
            except Exception as error:
                self.call_from_thread(self._set_status, f"Status: Error: {error}")
                return

            self.call_from_thread(
                self._reload_assistant_messages,
                response_message.message_id,
            )
            self.call_from_thread(self._reset_assistant_recording_state, "Status: Idle")

        self.run_worker(work, thread=True)

    def _on_assistant_prompt_editor_result(
        self,
        result: NoteEditResult | None,
        _original_prompt: SessionNote | None = None,
    ) -> None:
        if result is None or result.mode != "save" or result.text is None:
            return

        self._submit_assistant_prompt(result.text)

    def _reset_assistant_recording_state(self, status: str | None = "Status: Idle") -> None:
        self.recording_mode = "notes"
        self.recording_started_at = None
        self.stopping = False
        if status is not None:
            self._set_status(status)

    def _on_assistant_editor_result(
        self,
        result: NoteEditResult | None,
        original_message: AssistantMessage,
    ) -> None:
        if result is None or result.mode != "save" or result.text is None:
            return

        if self.assistant_store is None:
            self._set_status("Status: Error: assistant store is not ready")
            return

        try:
            if original_message.role == "user":
                updated_message = self.assistant_store.update_message(
                    original_message.message_id,
                    prompt=result.text,
                )
            else:
                updated_message = self.assistant_store.update_message(
                    original_message.message_id,
                    response=result.text,
                )
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        self._reload_assistant_messages(select_message_id=updated_message.message_id)
        self._set_status("Status: Saved")

    def _set_status(self, status: str) -> None:
        status_widget = self.query_one("#status", Static)
        status_widget.update(_format_status(status))

        for status_class in STATUS_CLASSES:
            status_widget.remove_class(status_class)
        status_widget.add_class(_status_class(status))
        if self.recording:
            self._toggle_status_blink(force=True)

    def _refresh_session_widgets(self) -> None:
        if self.session is None:
            return

        self.query_one("#session-title", Static).update(self.session.title)
        self.query_one("#session-description", Static).update(
            f"{self.session.slug} • {self.session.timestamp} • {len(self.notes)} notes"
        )
        self.query_one("#session-folder-path", SessionLink).update(
            f"Session folder: {self.session.session_dir}"
        )
        self.query_one("#session-folder-path", SessionLink).url = _transcript_url(
            self.session.session_dir,
            self.settings.editor,
        )
        self.query_one("#qr-code", Static).update(
            _render_qr_art(_qr_payload(self.session))
        )
        self.query_one("#notes-content", NoteTranscriptView).focus()

    def _refresh_settings_widgets(self) -> None:
        self.query_one("#settings-inputs", Static).update(
            "\n".join(
                [
                    "Input sources",
                    f"Audio device: {self.settings.audio_device or 'default'}",
                    f"Language: {self.settings.language}",
                    f"Model: {self.settings.model}",
                    f"Max recording seconds: {self.settings.max_recording_seconds}",
                ]
            )
        )
        self.query_one("#settings-outputs", Static).update(
            "\n".join(
                [
                    "Output sources",
                    f"Editor: {self.settings.editor}",
                    f"Keep audio: {self.settings.keep_audio}",
                    f"Append timestamps: {self.settings.append_timestamp}",
                    f"Audio folder: {self.settings.audio_output_folder or 'session/audio'}",
                    f"Text file: {self.settings.text_output_file or 'session/transcribe.txt'}",
                    f"JSON file: {self.settings.json_output_file or 'session/notes.json'}",
                ]
            )
        )
        self.query_one("#settings-runtime", Static).update(
            "\n".join(
                [
                    "Session runtime",
                    f"Base title: {self.settings.session_title}",
                    f"Current tab: {self.active_tab}",
                ]
            )
        )

    def _show_tab(self, tab: str) -> None:
        self.active_tab = tab
        try:
            self.query_one("#main-tabs", TabbedContent).active = tab
        except Exception:
            pass

        if tab == "assistant":
            try:
                self.query_one("#assistant-messages", AssistantMessageView).focus()
            except Exception:
                pass
        elif tab == "notes":
            try:
                self.query_one("#notes-content", NoteTranscriptView).focus()
            except Exception:
                pass

    def _workspace_tab(self) -> str:
        try:
            tabbed = self.query_one("#main-tabs", TabbedContent)
            return getattr(tabbed, "active", None) or self.active_tab
        except Exception:
            return self.active_tab

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        if event.tabbed_content.id != "main-tabs":
            return

        tab_id = getattr(event.tab, "id", "") or "notes"
        self.active_tab = tab_id
        self._refresh_settings_widgets()
        if tab_id == "notes":
            self.query_one("#notes-content", NoteTranscriptView).focus()
        elif tab_id == "assistant":
            try:
                self.query_one("#assistant-messages", AssistantMessageView).focus()
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "play-selected":
            self.action_play_note()
        elif event.button.id == "open-session":
            self.action_open_session()
        elif event.button.id == "open-session-session":
            self.action_open_session()
        elif event.button.id == "new-note":
            self.action_new_note()
        elif event.button.id == "edit-note":
            self.action_edit_note()
        elif event.button.id == "delete-note":
            self.action_delete_note()
        elif event.button.id == "zoom-in":
            self.action_zoom_in()
        elif event.button.id == "zoom-out":
            self.action_zoom_out()

    def _open_note_editor(self, title: str, note: SessionNote | None = None) -> None:
        initial_text = note.text if note is not None else ""
        self.push_screen(
            NoteEditorScreen(title=title, text=initial_text),
            callback=lambda result: self._on_note_editor_result(result, note),
        )

    def _on_note_editor_result(
        self,
        result: NoteEditResult | None,
        original_note: SessionNote | None,
    ) -> None:
        if result is None or result.mode != "save" or result.text is None:
            return

        if self.service is None or self.service.session_store is None:
            self._set_status("Status: Error: session store is not ready")
            return

        try:
            if original_note is None:
                saved_note = self.service.session_store.append_note(result.text)
            else:
                saved_note = self.service.session_store.update_note(
                    original_note.note_id,
                    result.text,
                )
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        self._reload_notes_from_store(select_note_id=saved_note.note_id)
        self._set_status("Status: Saved")

    def _reload_notes_from_store(self, select_note_id: str | None = None) -> None:
        if self.service is None or self.service.session_store is None:
            return

        self.notes = self.service.session_store.load_notes()
        self.selected_note_id = select_note_id or (
            self.notes[-1].note_id if self.notes else None
        )
        if self.selected_note_id is None:
            self.selection_anchor_index = None
            self.selection_end_index = None
        else:
            index = self._selected_note_index()
            self.selection_anchor_index = index
            self.selection_end_index = index
        self._render_notes()

    def _selected_note(self) -> SessionNote | None:
        if self.selected_note_id is None:
            return None

        if self.service is None or self.service.session_store is None:
            return None

        return self.service.session_store.get_note(self.selected_note_id)

    def _selected_assistant_message(self) -> AssistantMessage | None:
        if self.assistant_selected_message_id is None:
            return None

        if self.assistant_store is None:
            return None

        return self.assistant_store.get_message(self.assistant_selected_message_id)

    def _sync_selected_note(self) -> None:
        if not self.notes:
            self.selected_note_id = None
            self.selection_anchor_index = None
            self.selection_end_index = None
            return

        if self.selected_note_id is None:
            self.selected_note_id = self.notes[-1].note_id
            self.selection_anchor_index = len(self.notes) - 1
            self.selection_end_index = len(self.notes) - 1
            return

        for index, note in enumerate(self.notes):
            if note.note_id == self.selected_note_id:
                return

        self.selected_note_id = self.notes[-1].note_id
        self.selection_anchor_index = len(self.notes) - 1
        self.selection_end_index = len(self.notes) - 1

    def _sync_selected_assistant_message(self) -> None:
        if not self.assistant_messages:
            self.assistant_selected_message_id = None
            self.assistant_selection_anchor_index = None
            self.assistant_selection_end_index = None
            return

        if self.assistant_selected_message_id is None:
            self.assistant_selected_message_id = self.assistant_messages[-1].message_id
            self.assistant_selection_anchor_index = len(self.assistant_messages) - 1
            self.assistant_selection_end_index = len(self.assistant_messages) - 1
            return

        for index, message in enumerate(self.assistant_messages):
            if message.message_id == self.assistant_selected_message_id:
                return

        self.assistant_selected_message_id = self.assistant_messages[-1].message_id
        self.assistant_selection_anchor_index = len(self.assistant_messages) - 1
        self.assistant_selection_end_index = len(self.assistant_messages) - 1

    def _set_selected_note_by_index(
        self,
        index: int,
        extend_selection: bool = False,
    ) -> None:
        if not self.notes:
            self.selected_note_id = None
            self.selection_anchor_index = None
            self.selection_end_index = None
            return

        previous_index = self._selected_note_index()
        index = max(0, min(index, len(self.notes) - 1))
        self.selected_note_id = self.notes[index].note_id
        if extend_selection:
            if self.selection_anchor_index is None:
                self.selection_anchor_index = previous_index
            self.selection_end_index = index
        else:
            self.selection_anchor_index = index
            self.selection_end_index = index
        self._render_notes()

    def _move_note_selection(self, delta: int, extend_selection: bool = False) -> None:
        if not self.notes:
            return

        current_index = self._selected_note_index()
        next_index = max(0, min(len(self.notes) - 1, current_index + delta))
        self._set_selected_note_by_index(next_index, extend_selection=extend_selection)

    def _set_selected_assistant_message_by_index(
        self,
        index: int,
        extend_selection: bool = False,
    ) -> None:
        if not self.assistant_messages:
            self.assistant_selected_message_id = None
            self.assistant_selection_anchor_index = None
            self.assistant_selection_end_index = None
            return

        previous_index = self._assistant_selected_message_index()
        index = max(0, min(index, len(self.assistant_messages) - 1))
        self.assistant_selected_message_id = self.assistant_messages[index].message_id
        if extend_selection:
            if self.assistant_selection_anchor_index is None:
                self.assistant_selection_anchor_index = previous_index
            self.assistant_selection_end_index = index
        else:
            self.assistant_selection_anchor_index = index
            self.assistant_selection_end_index = index
        self._render_assistant_messages()

    def _move_assistant_message_selection(
        self, delta: int, extend_selection: bool = False
    ) -> None:
        if not self.assistant_messages:
            return

        current_index = self._assistant_selected_message_index()
        next_index = max(
            0, min(len(self.assistant_messages) - 1, current_index + delta)
        )
        self._set_selected_assistant_message_by_index(
            next_index,
            extend_selection=extend_selection,
        )

    def _selected_note_index(self) -> int:
        if self.selected_note_id is None:
            return 0

        for index, note in enumerate(self.notes):
            if note.note_id == self.selected_note_id:
                return index

        return 0

    def _assistant_selected_message_index(self) -> int:
        if self.assistant_selected_message_id is None:
            return 0

        for index, message in enumerate(self.assistant_messages):
            if message.message_id == self.assistant_selected_message_id:
                return index

        return 0

    def _selected_note_bounds(self) -> tuple[int, int] | None:
        if not self.notes or self.selected_note_id is None:
            return None

        start = self.selection_anchor_index
        end = self.selection_end_index
        if start is None or end is None:
            current_index = self._selected_note_index()
            return current_index, current_index

        return min(start, end), max(start, end)

    def _selected_notes_text(self) -> str:
        bounds = self._selected_note_bounds()
        if bounds is None:
            return ""

        start, end = bounds
        selected_notes = self.notes[start : end + 1]
        return "\n\n".join(
            note.text.strip() for note in selected_notes if note.text.strip()
        )

    def _selected_assistant_message_bounds(self) -> tuple[int, int] | None:
        if not self.assistant_messages or self.assistant_selected_message_id is None:
            return None

        start = self.assistant_selection_anchor_index
        end = self.assistant_selection_end_index
        if start is None or end is None:
            current_index = self._assistant_selected_message_index()
            return current_index, current_index

        return min(start, end), max(start, end)

    def _selected_assistant_messages_text(self) -> str:
        bounds = self._selected_assistant_message_bounds()
        if bounds is None:
            return ""

        start, end = bounds
        selected_messages = self.assistant_messages[start : end + 1]
        return "\n\n".join(
            (
                message.prompt.strip()
                if message.role == "user"
                else message.response.strip()
            )
            for message in selected_messages
            if (
                message.prompt.strip() if message.role == "user" else message.response.strip()
            )
        )

    def _update_detail_panel(self) -> None:
        try:
            detail = self.query_one("#note-detail", Static)
        except Exception:
            return

        note = self._selected_note()
        if note is None:
            detail.update("No note selected.")
            return

        audio = str(note.audio_file) if note.audio_file is not None else "No audio"
        detail.update(
            "\n".join(
                [
                    f"Time: {note.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"Audio: {audio}",
                    "",
                    note.text,
                ]
            )
        )

    def _set_recording_theme(self, recording: bool) -> None:
        self.screen.set_class(recording, "recording")
        self._status_blink_state = False
        if not recording:
            self.query_one("#status", Static).remove_class("status-recording-alt")

    def _toggle_status_blink(self, force: bool = False) -> None:
        if not self.recording and not force:
            return

        self._status_blink_state = not self._status_blink_state
        status_widget = self.query_one("#status", Static)
        if self._status_blink_state:
            status_widget.add_class("status-recording-alt")
        else:
            status_widget.remove_class("status-recording-alt")

    def _set_note_zoom(self, value: int) -> None:
        self.note_zoom = value
        self._render_notes()


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


def _transcript_url(
    target: VoiceNoteSession | Path | None, editor: str = "code"
) -> str | None:
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


def _render_qr_art(target: Path | str) -> str:
    payload = str(target)
    try:
        import qrcode

        qr = qrcode.QRCode(border=0, box_size=1)
        qr.add_data(payload)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        return "\n".join(
            "".join("██" if cell else "  " for cell in row) for row in matrix
        )
    except Exception:
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        rows = []
        bits = bin(int(digest, 16))[2:].zfill(256)
        width = 16
        for row_index in range(16):
            row_bits = bits[row_index * width : (row_index + 1) * width]
            rows.append("".join("██" if bit == "1" else "  " for bit in row_bits))
        rows.append("")
        rows.append(payload)
        return "\n".join(rows)


def _qr_payload(session: VoiceNoteSession) -> str:
    return session.folder_name


class SessionLink(Link):
    async def _on_click(self, event: events.Click) -> None:
        await super()._on_click(event)
        if event.widget is self:
            self.app.action_open_session()
            event.stop()

    def action_open_link(self) -> None:
        self.app.action_open_session()
