from textual.app import ComposeResult
from textual.widgets import Input

from src.app.ui.widgets.form_field import FormField


class PathInput(FormField):
    input_class = Input

    def __init__(self, label: str, value: str = "", **kwargs) -> None:
        self.input_id = f"{kwargs.get('id')}-input" if kwargs.get("id") else None
        super().__init__(
            label,
            self.input_widget(value, id=self.input_id),
            **kwargs,
        )

    @staticmethod
    def input_widget(value: str = "", id: str | None = None) -> Input:
        return Input(value=value, id=id)

    def compose(self) -> ComposeResult:
        yield from super().compose()
