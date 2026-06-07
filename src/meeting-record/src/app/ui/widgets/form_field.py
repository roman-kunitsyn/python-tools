from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label


class FormField(Vertical):
    def __init__(self, label: str, field: Widget, *children, **kwargs) -> None:
        super().__init__(*children, **kwargs)
        self.label = label
        self.field = field
        self.add_class("form-field")

    def compose(self) -> ComposeResult:
        yield Label(self.label)
        yield self.field
