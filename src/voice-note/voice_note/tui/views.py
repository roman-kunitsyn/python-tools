from __future__ import annotations

from textual.containers import VerticalScroll
from textual.widgets import Static
from rich import box
from rich.panel import Panel
from rich.text import Text

from voice_note.models.assistant_message import AssistantMessage
from voice_note.models.session_note import SessionNote
from voice_note.tui.components import render_assistant_message_card, render_note_card


class NoteTranscriptView(VerticalScroll):
    def render_notes(
        self,
        notes: list[SessionNote],
        selected_note_id: str | None = None,
        selected_note_bounds: tuple[int, int] | None = None,
        zoom: int = 1,
    ) -> None:
        self.remove_children()

        if not notes:
            self.mount(
                NoteCard(
                    note_id="empty-notes",
                    renderable=Panel(
                        Text("No notes yet."),
                        border_style="grey37",
                        box=box.ROUNDED,
                        padding=(1, 2),
                        expand=True,
                    ),
                )
            )
            self.call_after_refresh(self.scroll_home)
            return

        for index, note in enumerate(notes, start=1):
            in_selection = False
            if selected_note_bounds is not None:
                start, end = selected_note_bounds
                in_selection = start <= (index - 1) <= end

            card = NoteCard(
                note_id=note.note_id,
                renderable=render_note_card(
                    note,
                    index,
                    note.note_id == selected_note_id,
                    in_selection,
                    zoom,
                ),
            )
            self.mount(card)

        if selected_note_id is not None:
            self.call_after_refresh(self._scroll_to_note, selected_note_id)
        else:
            self.call_after_refresh(self.scroll_home)

    def _scroll_to_note(self, note_id: str) -> None:
        for child in self.children:
            if isinstance(child, NoteCard) and child.note_id == note_id:
                self.scroll_to_widget(child, center=True)
                return

        if self.children:
            try:
                self.scroll_to_widget(self.children[0], center=True)
            except Exception:
                pass
            return

        try:
            self.scroll_home()
        except Exception:
            return


class NoteCard(Static):
    def __init__(self, note_id: str, renderable: Panel) -> None:
        super().__init__(renderable)
        self.note_id = note_id


class AssistantMessageView(VerticalScroll):
    def render_messages(
        self,
        messages: list[AssistantMessage],
        selected_message_id: str | None = None,
        selected_message_bounds: tuple[int, int] | None = None,
        zoom: int = 1,
    ) -> None:
        self.remove_children()

        if not messages:
            self.mount(
                AssistantMessageCard(
                    message_id="empty-messages",
                    renderable=Panel(
                        Text("No assistant messages yet."),
                        border_style="grey37",
                        box=box.ROUNDED,
                        padding=(1, 2),
                        expand=True,
                    ),
                )
            )
            self.call_after_refresh(self.scroll_home)
            return

        for index, message in enumerate(messages, start=1):
            in_selection = False
            if selected_message_bounds is not None:
                start, end = selected_message_bounds
                in_selection = start <= (index - 1) <= end

            card = AssistantMessageCard(
                message_id=message.message_id,
                renderable=render_assistant_message_card(
                    message,
                    index,
                    message.message_id == selected_message_id,
                    in_selection,
                    zoom,
                ),
            )
            self.mount(card)

        if selected_message_id is not None:
            self.call_after_refresh(self._scroll_to_message, selected_message_id)
        else:
            self.call_after_refresh(self.scroll_home)

    def _scroll_to_message(self, message_id: str) -> None:
        for child in self.children:
            if isinstance(child, AssistantMessageCard) and child.message_id == message_id:
                self.scroll_to_widget(child, center=True)
                return

        if self.children:
            try:
                self.scroll_to_widget(self.children[0], center=True)
            except Exception:
                pass
            return

        try:
            self.scroll_home()
        except Exception:
            return


class AssistantMessageCard(Static):
    def __init__(self, message_id: str, renderable: Panel) -> None:
        super().__init__(renderable)
        self.message_id = message_id
