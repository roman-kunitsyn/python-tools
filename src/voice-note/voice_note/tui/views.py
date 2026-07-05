from __future__ import annotations

from textual.containers import VerticalScroll
from textual.widgets import Static
from rich import box
from rich.panel import Panel
from rich.text import Text

from voice_note.models.session_note import SessionNote
from voice_note.tui.components import render_note_card


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
