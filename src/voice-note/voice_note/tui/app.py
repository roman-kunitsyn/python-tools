import math
import hashlib
import re
import subprocess
import time
from typing import Callable
from pathlib import Path
from urllib.parse import quote

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.timer import Timer
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Link,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from voice_note.config import DEFAULT_CONFIG_FILE, VoiceNoteConfigStore
from voice_note.audio.player import AudioPlaybackController
from voice_note.models.assistant_message import AssistantMessage
from voice_note.models.session import VoiceNoteSession
from voice_note.models.session import build_session_folder_name
from voice_note.models.session_note import SessionNote
from voice_note.models.settings import (
    DEFAULT_ASSISTANT_MODEL,
    DEFAULT_AUDIO_DEVICE,
    DEFAULT_EDITOR,
    DEFAULT_MAX_RECORDING_SECONDS,
    DEFAULT_SESSION_TITLE,
    build_timestamp,
    VoiceNoteSettings,
)
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
from voice_note.transcription.whisper_transcriber import DEFAULT_MODEL_DIR


STATUS_CLASSES = (
    "status-idle",
    "status-recording",
    "status-transcribing",
    "status-saved",
    "status-overflow",
    "status-error",
)


class RefreshingSelect(Select[str]):
    def __init__(
        self,
        options: list[tuple[str, str]],
        *,
        options_provider: Callable[[], list[tuple[str, str]]],
        prompt: str = "Select",
        allow_blank: bool = True,
        value: str | Select.NoSelection = Select.NULL,
        type_to_search: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        tooltip=None,
        compact: bool = False,
    ) -> None:
        super().__init__(
            options,
            prompt=prompt,
            allow_blank=allow_blank,
            value=value,
            type_to_search=type_to_search,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            tooltip=tooltip,
            compact=compact,
        )
        self._options_provider = options_provider

    def refresh_options(self) -> None:
        options = self._options_provider()
        if not self.is_mounted:
            self._setup_variables_for_options(options)
            return

        self.set_options(options)

    def action_show_overlay(self) -> None:
        self.refresh_options()
        super().action_show_overlay()


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

    #settings-form {
        height: 1fr;
        margin-top: 1;
        padding-right: 1;
    }

    #settings-tabs {
        height: 1fr;
        margin-top: 1;
    }

    #settings-core-form,
    #settings-output-form,
    #settings-session-form {
        height: 1fr;
        padding-right: 1;
    }

    #settings-actions {
        height: auto;
        margin-top: 1;
    }

    .settings-section-title {
        margin-top: 1;
        margin-bottom: 1;
        text-style: bold;
    }

    .settings-row {
        height: auto;
        margin-bottom: 1;
    }

    .settings-label {
        width: 28;
        padding-right: 1;
        color: $text-muted;
    }

    .settings-input,
    .settings-select {
        width: 1fr;
    }

    .settings-note {
        color: $text-muted;
        margin-top: 1;
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
        ("s", "stop_playback", "Stop Playback"),
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
        ("ctrl+s", "save_notes", "Save"),
        ("escape", "quit", "Exit"),
        ("ctrl+c", "quit", "Exit"),
    ]

    def __init__(
        self,
        settings: VoiceNoteSettings,
        session_service: SessionService,
        config_file: Path | None = None,
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
        self.audio_player = AudioPlaybackController()
        self.config_store = VoiceNoteConfigStore(config_file or DEFAULT_CONFIG_FILE)
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
                    with Vertical(id="settings-view"):
                        yield Static("Settings", id="settings-title")
                        yield Static(
                            f"Saved config file: {self.config_store.config_file}",
                            id="settings-config-path",
                        )
                        with TabbedContent(initial="settings-core", id="settings-tabs"):
                            with TabPane("Core", id="settings-core"):
                                yield self._settings_core_tab()
                            with TabPane("Output", id="settings-output"):
                                yield self._settings_output_tab()
                            with TabPane("Session", id="settings-session"):
                                yield self._settings_session_tab()
                        yield Horizontal(
                            Button(
                                "Save Config",
                                variant="primary",
                                id="save-config",
                            ),
                            Button(
                                "Load Config",
                                id="load-config",
                            ),
                            id="settings-actions",
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
            ollama_client=OllamaClient(model=self.settings.assistant_model),
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
        if self._workspace_tab() == "settings":
            self.action_save_config()
            return

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

        try:
            if note.audio_file is not None:
                state = self.audio_player.play_audio_file(note.audio_file)
            else:
                state = self.audio_player.speak_text(note.text)
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        self._set_status(_playback_status_message(state))

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

    def action_stop_playback(self) -> None:
        state = self.audio_player.stop()
        if state == "idle":
            self._set_status("Status: Idle")
        else:
            self._set_status("Status: Stopped")

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

        try:
            if message.role == "user" and message.source_audio is not None:
                state = self.audio_player.play_audio_file(message.source_audio)
            else:
                text = message.response if message.role != "user" else message.prompt
                if text.strip() == "":
                    raise RuntimeError("assistant message has no text to play")
                state = self.audio_player.speak_text(text)
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        self._set_status(_playback_status_message(state))

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
                self._regenerate_assistant_response(updated_message)
                return
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

    def _regenerate_assistant_response(self, prompt_message: AssistantMessage) -> None:
        if self.assistant_service is None or self.assistant_store is None:
            self._set_status("Status: Error: assistant is not ready")
            return

        messages = self.assistant_store.load_messages()
        prompt_index = next(
            (
                index
                for index, message in enumerate(messages)
                if message.message_id == prompt_message.message_id
            ),
            None,
        )
        if prompt_index is None:
            self._set_status("Status: Error: assistant prompt not found")
            return

        next_message = messages[prompt_index + 1] if prompt_index + 1 < len(messages) else None
        self._set_status("Status: Generating assistant response...")

        def work() -> None:
            try:
                response_text = self.assistant_service.generate_response_text(
                    prompt_message.prompt
                )
            except Exception as error:
                self.call_from_thread(self._set_status, f"Status: Error: {error}")
                return

            try:
                if next_message is not None and next_message.role == "assistant":
                    updated_response = self.assistant_store.update_message(
                        next_message.message_id,
                        prompt=prompt_message.prompt,
                        response=response_text,
                        response_state="complete",
                    )
                    self.call_from_thread(
                        self._reload_assistant_messages,
                        updated_response.message_id,
                    )
                else:
                    created_response = self.assistant_store.append_message(
                        role="assistant",
                        prompt=prompt_message.prompt,
                        response=response_text,
                        response_state="complete",
                        source_audio=prompt_message.source_audio,
                    )
                    self.call_from_thread(
                        self._reload_assistant_messages,
                        created_response.message_id,
                    )
            except Exception as error:
                self.call_from_thread(self._set_status, f"Status: Error: {error}")
                return

            self.call_from_thread(self._set_status, "Status: Saved")

        self.run_worker(work, thread=True)

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
        self._sync_settings_form()

    def _sync_settings_form(self) -> None:
        self._set_select_value("setting-mode", self.settings.mode)
        self._set_select_value("setting-verbose", self.settings.verbose)
        self._set_select_value(
            "setting-audio-device",
            self._audio_device_value(),
            options=self._audio_device_options(self._audio_device_value()),
        )
        self._set_input_value("setting-language", self._language_value())
        self._set_select_value(
            "setting-model",
            self._model_value(),
            options=self._model_options(self._model_value()),
        )
        self._set_select_value(
            "setting-assistant-model",
            self._assistant_model_value(),
            options=self._assistant_model_options(self._assistant_model_value()),
        )
        self._set_select_value(
            "setting-max-recording-seconds",
            self._max_recording_seconds_value(),
        )
        self._set_select_value("setting-keep-audio", self.settings.keep_audio)
        self._set_select_value(
            "setting-append-timestamp",
            self.settings.append_timestamp,
        )
        self._set_select_value("setting-editor", self._editor_value())
        self._set_input_value(
            "setting-audio-output-folder", self._audio_output_folder_value()
        )
        self._set_input_value(
            "setting-text-output-file", self._text_output_file_value()
        )
        self._set_input_value(
            "setting-json-output-file", self._json_output_file_value()
        )
        self._set_input_value("setting-log-file", self._log_file_value())
        self._set_input_value("setting-session-title", self._session_title_value())
        self._set_input_value("setting-timestamp-format", self.settings.timestamp_format)

    def _settings_row(self, label: str, widget) -> Horizontal:
        return Horizontal(
            Static(label, classes="settings-label"),
            widget,
            classes="settings-row",
        )

    def _settings_core_tab(self) -> VerticalScroll:
        return VerticalScroll(
            Static("Core", classes="settings-section-title"),
            self._settings_row(
                "Mode",
                Select(
                    [("CLI", "cli"), ("TUI", "tui")],
                    prompt="Choose mode",
                    value=self.settings.mode,
                    id="setting-mode",
                ),
            ),
            self._settings_row(
                "Verbose",
                Select(
                    [("Off", False), ("On", True)],
                    prompt="Verbose logging",
                    value=self.settings.verbose,
                    id="setting-verbose",
                ),
            ),
            self._settings_row(
                "Audio device",
                RefreshingSelect(
                    self._audio_device_options(self.settings.audio_device or "default"),
                    options_provider=lambda: self._audio_device_options(
                        self.settings.audio_device or "default"
                    ),
                    prompt="Choose device",
                    value=self.settings.audio_device or "default",
                    id="setting-audio-device",
                ),
            ),
            self._settings_row(
                "Whisper language",
                Input(
                    value=self.settings.language,
                    id="setting-language",
                ),
            ),
            self._settings_row(
                "Whisper model",
                RefreshingSelect(
                    self._model_options(self.settings.model),
                    options_provider=lambda: self._model_options(
                        self._model_value()
                    ),
                    prompt="Choose model",
                    value=self._model_value(),
                    id="setting-model",
                ),
            ),
            self._settings_row(
                "Ollama model",
                Select(
                    self._assistant_model_options(self.settings.assistant_model),
                    prompt="Choose model",
                    value=self.settings.assistant_model,
                    id="setting-assistant-model",
                ),
            ),
            self._settings_row(
                "Max recording seconds",
                Select(
                    self._recording_limit_options(self.settings.max_recording_seconds),
                    prompt="Choose limit",
                    value=self.settings.max_recording_seconds,
                    id="setting-max-recording-seconds",
                ),
            ),
            id="settings-core-form",
        )

    def _settings_output_tab(self) -> VerticalScroll:
        return VerticalScroll(
            Static("Output", classes="settings-section-title"),
            self._settings_row(
                "Keep audio",
                Select(
                    [("No", False), ("Yes", True)],
                    prompt="Keep audio",
                    value=self.settings.keep_audio,
                    id="setting-keep-audio",
                ),
            ),
            self._settings_row(
                "Append timestamp",
                Select(
                    [("No", False), ("Yes", True)],
                    prompt="Append timestamp",
                    value=self.settings.append_timestamp,
                    id="setting-append-timestamp",
                ),
            ),
            self._settings_row(
                "Editor",
                Select(
                    [("code", "code"), ("nvim", "nvim")],
                    prompt="Choose editor",
                    value=self.settings.editor,
                    id="setting-editor",
                ),
            ),
                            self._settings_row(
                                "Audio output folder",
                                Input(
                                    value=self._audio_output_folder_value(),
                                    placeholder=self._audio_output_folder_placeholder(),
                                    id="setting-audio-output-folder",
                                ),
                            ),
                            self._settings_row(
                                "Text output file",
                                Input(
                                    value=self._text_output_file_value(),
                                    placeholder=self._text_output_file_placeholder(),
                                    id="setting-text-output-file",
                                ),
                            ),
                            self._settings_row(
                                "JSON output file",
                                Input(
                                    value=self._json_output_file_value(),
                                    placeholder=self._json_output_file_placeholder(),
                                    id="setting-json-output-file",
                                ),
                            ),
                            self._settings_row(
                                "Log file",
                                Input(
                                    value=self._log_file_value(),
                                    placeholder=self._log_file_placeholder(),
                                    id="setting-log-file",
                                ),
                            ),
            id="settings-output-form",
        )

    def _settings_session_tab(self) -> VerticalScroll:
        return VerticalScroll(
            Static("Session", classes="settings-section-title"),
            self._settings_row(
                "Session title",
                Input(
                    value=self.settings.session_title,
                    id="setting-session-title",
                ),
            ),
            self._settings_row(
                "Timestamp format",
                Input(
                    value=self.settings.timestamp_format,
                    id="setting-timestamp-format",
                ),
            ),
            Static(
                "Session folders still come from the session picker or --session; config saves runtime defaults only.",
                classes="settings-note",
            ),
            id="settings-session-form",
        )

    def _model_options(self, current_value: str) -> list[tuple[str, str]]:
        models = discover_local_whisper_models()
        if not models:
            return [(current_value, current_value)]

        options = [(label, value) for label, value in models]
        if current_value not in {value for _, value in options}:
            options.insert(0, (current_value, current_value))
        return options

    def _audio_device_options(self, current_value: str) -> list[tuple[str, str]]:
        devices = discover_local_audio_devices()
        if not devices:
            return [(current_value, current_value)]

        options = [(label, value) for label, value in devices]
        if current_value not in {value for _, value in options}:
            options.insert(0, (current_value, current_value))
        return options

    def _audio_device_value(self) -> str:
        return self.settings.audio_device or DEFAULT_AUDIO_DEVICE

    def _language_value(self) -> str:
        return self.settings.language or "auto"

    def _model_value(self) -> str:
        return self.settings.model or "small"

    def _assistant_model_value(self) -> str:
        return self.settings.assistant_model or DEFAULT_ASSISTANT_MODEL

    def _max_recording_seconds_value(self) -> int:
        return self.settings.max_recording_seconds or DEFAULT_MAX_RECORDING_SECONDS

    def _editor_value(self) -> str:
        return self.settings.editor or DEFAULT_EDITOR

    def _session_title_value(self) -> str:
        return self.settings.session_title or DEFAULT_SESSION_TITLE

    def _audio_output_folder_value(self) -> str:
        if self.settings.audio_output_folder is not None:
            return str(self.settings.audio_output_folder)
        if self.session is not None:
            return str(self.session.audio_dir)
        return ""

    def _audio_output_folder_placeholder(self) -> str:
        return self._session_path_hint("audio")

    def _text_output_file_value(self) -> str:
        if self.settings.text_output_file is not None:
            return str(self.settings.text_output_file)
        if self.session is not None:
            return str(self.session.transcript_file)
        return ""

    def _text_output_file_placeholder(self) -> str:
        return self._session_path_hint("transcribe.txt")

    def _json_output_file_value(self) -> str:
        if self.settings.json_output_file is not None:
            return str(self.settings.json_output_file)
        if self.session is not None:
            return str(self.session.notes_file)
        return ""

    def _json_output_file_placeholder(self) -> str:
        return self._session_path_hint("notes.json")

    def _log_file_value(self) -> str:
        if self.settings.log_file is not None:
            return str(self.settings.log_file)
        if self.session is not None:
            return str(self.session.log_file)
        return ""

    def _log_file_placeholder(self) -> str:
        return self._session_path_hint("log.txt")

    def _session_path_hint(self, suffix: str) -> str:
        folder_name = self._session_folder_name_hint()
        return f"logs/voice_notes/{folder_name}/{suffix}"

    def _session_folder_name_hint(self) -> str:
        if self.session is not None:
            return self.session.session_dir.name
        if self.settings.session_dir is not None:
            return self.settings.session_dir.name
        return build_session_folder_name(
            self._session_title_value(),
            build_timestamp(self.settings.timestamp_format),
        )

    def _assistant_model_options(self, current_value: str) -> list[tuple[str, str]]:
        models = discover_local_ollama_models()
        if not models:
            return [(current_value, current_value)]

        options = [(label, value) for label, value in models]
        if current_value not in {value for _, value in options}:
            options.insert(0, (current_value, current_value))
        return options

    def _recording_limit_options(self, current_value: int) -> list[tuple[str, int]]:
        presets = [30, 60, 90, 120, 180, 300]
        values = [current_value] + [preset for preset in presets if preset != current_value]
        return [(f"{value}", value) for value in values]

    def _set_select_value(
        self,
        widget_id: str,
        value: object,
        options: list[tuple[str, object]] | None = None,
    ) -> None:
        try:
            widget = self.query_one(f"#{widget_id}", Select)
        except Exception:
            return

        if options is not None:
            widget.set_options(options)
        widget.value = value

    def _set_input_value(self, widget_id: str, value: object | None) -> None:
        try:
            widget = self.query_one(f"#{widget_id}", Input)
        except Exception:
            return

        widget.value = "" if value is None else str(value)

    def _replace_settings(self, **updates: object) -> VoiceNoteSettings:
        return self.settings.__class__(**{**self.settings.__dict__, **updates})

    def _focus_settings_tabs(self) -> None:
        try:
            tabs = self.query_one("#settings-tabs", TabbedContent)
        except Exception:
            return

        try:
            tabs.focus()
        except Exception:
            self.call_after_refresh(tabs.focus)

    def action_save_config(self) -> None:
        try:
            saved_file = self.config_store.save(self.settings)
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        self._set_status(f"Status: Saved config to {saved_file}")

    def action_load_config(self) -> None:
        try:
            loaded = self.config_store.load()
        except Exception as error:
            self._set_status(f"Status: Error: {error}")
            return

        if loaded is None:
            self._set_status(f"Status: Error: missing config file at {self.config_store.config_file}")
            return

        self.settings = loaded
        self._sync_settings_form()
        self._set_status(f"Status: Loaded config from {self.config_store.config_file}")

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
        elif tab == "settings":
            self._focus_settings_tabs()

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
        if tab_id.startswith("--content-tab-"):
            tab_id = tab_id.removeprefix("--content-tab-")
        self.active_tab = tab_id
        self._refresh_settings_widgets()
        if tab_id == "notes":
            self.query_one("#notes-content", NoteTranscriptView).focus()
        elif tab_id == "assistant":
            try:
                self.query_one("#assistant-messages", AssistantMessageView).focus()
            except Exception:
                pass
        elif tab_id == "settings":
            self._focus_settings_tabs()

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
        elif event.button.id == "save-config":
            self.action_save_config()
        elif event.button.id == "load-config":
            self.action_load_config()

    def on_input_changed(self, event: Input.Changed) -> None:
        widget_id = event.input.id or ""
        if widget_id == "setting-language":
            self.settings = self._replace_settings(language=event.value or "auto")
        elif widget_id == "setting-audio-output-folder":
            self.settings = self._replace_settings(
                audio_output_folder=Path(event.value) if event.value else None
            )
        elif widget_id == "setting-text-output-file":
            self.settings = self._replace_settings(
                text_output_file=Path(event.value) if event.value else None
            )
        elif widget_id == "setting-json-output-file":
            self.settings = self._replace_settings(
                json_output_file=Path(event.value) if event.value else None
            )
        elif widget_id == "setting-log-file":
            self.settings = self._replace_settings(
                log_file=Path(event.value) if event.value else None
            )
        elif widget_id == "setting-session-title":
            self.settings = self._replace_settings(
                session_title=event.value or self.settings.session_title
            )
        elif widget_id == "setting-timestamp-format":
            self.settings = self._replace_settings(
                timestamp_format=event.value or self.settings.timestamp_format
            )

    def on_select_changed(self, event: Select.Changed) -> None:
        widget_id = event.select.id or ""
        if widget_id == "setting-mode":
            self.settings = self._replace_settings(mode=str(event.value))
        elif widget_id == "setting-verbose":
            self.settings = self._replace_settings(verbose=bool(event.value))
        elif widget_id == "setting-audio-device":
            self._update_audio_device(str(event.value))
        elif widget_id == "setting-model":
            self._update_whisper_model(str(event.value))
        elif widget_id == "setting-assistant-model":
            self.settings = self._replace_settings(assistant_model=str(event.value))
        elif widget_id == "setting-max-recording-seconds":
            self.settings = self._replace_settings(
                max_recording_seconds=int(event.value)
            )
        elif widget_id == "setting-keep-audio":
            self.settings = self._replace_settings(keep_audio=bool(event.value))
        elif widget_id == "setting-append-timestamp":
            self.settings = self._replace_settings(
                append_timestamp=bool(event.value)
            )
        elif widget_id == "setting-editor":
            self.settings = self._replace_settings(editor=str(event.value))

    def _update_audio_device(self, audio_device: str) -> None:
        self.settings = self._replace_settings(audio_device=audio_device)
        if self.service is not None and hasattr(self.service, "recorder"):
            recorder = self.service.recorder
            if hasattr(recorder, "audio_device"):
                recorder.audio_device = audio_device

    def _update_whisper_model(self, model: str) -> None:
        self.settings = self._replace_settings(model=model)
        if self.service is not None and hasattr(self.service, "transcriber"):
            transcriber = self.service.transcriber
            if hasattr(transcriber, "model"):
                transcriber.model = model

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


def _playback_status_message(state: str) -> str:
    if state == "paused":
        return "Status: Paused"
    if state == "playing":
        return "Status: Playing"
    if state == "stopped":
        return "Status: Stopped"
    return "Status: Idle"


def _format_settings_sections(
    settings: VoiceNoteSettings,
    current_tab: str,
) -> dict[str, str]:
    inputs = "\n".join(
        [
            "Input settings",
            _setting_line(
                "mode",
                settings.mode,
                "Run mode for the app: cli or tui.",
            ),
            _setting_line(
                "verbose",
                settings.verbose,
                "Enable debug logging and extra runtime output.",
            ),
            _setting_line(
                "audio_device",
                settings.audio_device or "default",
                "Microphone name or device id used by recording.",
            ),
            _setting_line(
                "language",
                settings.language,
                "Whisper language hint for transcription.",
            ),
            _setting_line(
                "model",
                settings.model,
                "Whisper transcription model or direct model file path.",
            ),
            _setting_line(
                "assistant_model",
                settings.assistant_model,
                "Ollama model used by the Assistant tab.",
            ),
            _setting_line(
                "max_recording_seconds",
                settings.max_recording_seconds,
                "Maximum length of one push-to-talk recording.",
            ),
        ]
    )
    outputs = "\n".join(
        [
            "Output and storage",
            _setting_line(
                "audio_output_folder",
                settings.audio_output_folder or "session/audio",
                "Folder where recorded audio is saved when audio is kept.",
            ),
            _setting_line(
                "keep_audio",
                settings.keep_audio,
                "Keep or delete recorded audio after transcription.",
            ),
            _setting_line(
                "text_output_file",
                settings.text_output_file or "session/transcribe.txt",
                "Human-readable transcript file for note text.",
            ),
            _setting_line(
                "json_output_file",
                settings.json_output_file or "session/notes.json",
                "Rewriteable JSON store for note entries.",
            ),
            _setting_line(
                "append_timestamp",
                settings.append_timestamp,
                "Write timestamps into the rendered transcript text.",
            ),
            _setting_line(
                "editor",
                settings.editor,
                "Editor used when opening transcript files from the TUI.",
            ),
            _setting_line(
                "log_file",
                settings.log_file or "session/log.txt",
                "Session log for Whisper, ffmpeg, and other technical output.",
            ),
        ]
    )
    runtime = "\n".join(
        [
            "Session and runtime",
            _setting_line(
                "session_title",
                settings.session_title,
                "Human-friendly title used when creating a new session folder.",
            ),
            _setting_line(
                "timestamp_format",
                settings.timestamp_format,
                "strftime format used when generating new session timestamps.",
            ),
            _setting_line(
                "session_dir",
                settings.session_dir or "derived from session title and timestamp",
                "Explicit session folder override when loading or creating a session.",
            ),
            _setting_line(
                "audio_file",
                settings.audio_file or "auto-generated per recording",
                "Explicit output path for a recording if you want to override the default.",
            ),
            _setting_line(
                "current_tab",
                current_tab,
                "Currently active TUI tab.",
            ),
        ]
    )
    return {"inputs": inputs, "outputs": outputs, "runtime": runtime}


def _setting_line(name: str, value: object, description: str) -> str:
    return f"{name}: {value} — {description}"


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


def discover_local_audio_devices() -> list[tuple[str, str]]:
    try:
        completed = subprocess.run(
            ["ffmpeg", "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return []

    output = completed.stderr or completed.stdout
    devices = _parse_ffmpeg_audio_devices(output)
    return devices


def discover_local_whisper_models() -> list[tuple[str, str]]:
    if not DEFAULT_MODEL_DIR.exists():
        return []

    models: list[tuple[str, str]] = []
    for model_file in sorted(DEFAULT_MODEL_DIR.glob("ggml-*.bin")):
        if not model_file.is_file():
            continue

        model_name = _whisper_model_name(model_file)
        models.append((f"{model_name} ({_format_file_size(model_file.stat().st_size)})", model_name))
    return models


def discover_local_ollama_models() -> list[tuple[str, str]]:
    try:
        completed = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    models: list[tuple[str, str]] = []
    for line in completed.stdout.splitlines():
        parsed = _parse_ollama_list_line(line)
        if parsed is not None:
            models.append(parsed)
    return models


def _parse_ffmpeg_audio_devices(output: str) -> list[tuple[str, str]]:
    devices: list[tuple[str, str]] = []
    in_audio_section = False
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lowered = line.lower()
        if "audio devices" in lowered:
            in_audio_section = True
            continue

        if in_audio_section and "video devices" in lowered:
            in_audio_section = False
            continue

        if not in_audio_section:
            continue

        match = re.search(r"\[(?P<index>\d+)\]\s+(?P<name>.+)", line)
        if match is None:
            continue

        index = match.group("index").strip()
        name = match.group("name").strip()
        if not name:
            continue

        devices.append((f"{name} [{index}]", name))

    return devices


def _whisper_model_name(model_file: Path) -> str:
    stem = model_file.stem
    if stem.startswith("ggml-"):
        return stem.removeprefix("ggml-")
    return stem


def _format_file_size(num_bytes: int) -> str:
    size = float(max(0, num_bytes))
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} B"
            if size.is_integer():
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024


def _parse_ollama_list_line(line: str) -> tuple[str, str] | None:
    normalized = line.strip()
    if not normalized or normalized.upper().startswith("NAME "):
        return None

    parts = re.split(r"\s{2,}", normalized)
    if len(parts) < 3:
        return None

    name = parts[0].strip()
    size = parts[2].strip()
    if not name or not size:
        return None

    return (f"{name} ({size})", name)


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
