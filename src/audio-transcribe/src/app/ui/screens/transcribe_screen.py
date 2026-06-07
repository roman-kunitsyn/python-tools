from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Header, Static

from src.app.ui.forms.transcribe_form import TranscribeForm
from src.app.ui.screens.progress_screen import ProgressScreen
from src.app.ui.widgets.footer_bar import FooterBar


class TranscribeScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            TranscribeForm(id="transcribe-form"),
            Static("", id="status"),
            id="content",
        )
        yield FooterBar()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.app.exit()
            return

        if event.button.id == "start":
            form = self.query_one("#transcribe-form", TranscribeForm)

            try:
                config = form.build_config()
            except ValueError as error:
                self.query_one("#status", Static).update(f"Validation error: {error}")
                return

            self.app.config = config
            self.app.push_screen(ProgressScreen(config))
