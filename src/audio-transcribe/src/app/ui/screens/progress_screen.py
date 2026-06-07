import subprocess

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label, LoadingIndicator, Static

from src.app.models.config import TranscribeConfig
from src.app.services.transcriber import TranscribeService
from src.app.ui.widgets.footer_bar import FooterBar


class ProgressScreen(Screen):
    def __init__(self, config: TranscribeConfig) -> None:
        super().__init__()
        self.config = config

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Transcribing...", id="title"),
            LoadingIndicator(id="loading"),
            Static("", id="status"),
            Button("Back", id="back"),
            id="content",
        )
        yield FooterBar()

    def on_mount(self) -> None:
        self.query_one("#back", Button).styles.display = "none"
        self.run_worker(self._run_transcription, thread=True)

    def _run_transcription(self) -> None:
        service = TranscribeService()

        try:
            transcript_file = service.transcribe(self.config)
        except ValueError as error:
            self.app.call_from_thread(self._show_result, f"Validation error: {error}")
        except FileNotFoundError as error:
            self.app.call_from_thread(self._show_result, f"Whisper failed: {error}")
        except subprocess.CalledProcessError as error:
            self.app.call_from_thread(
                self._show_result,
                f"Whisper failed with exit code {error.returncode}.",
            )
        else:
            self.app.call_from_thread(
                self._show_result,
                f"Transcription written to: {transcript_file}",
            )

    def _show_result(self, message: str) -> None:
        self.query_one("#title", Label).update("Finished")
        self.query_one("#loading", LoadingIndicator).styles.display = "none"
        self.query_one("#status", Static).update(message)
        self.query_one("#back", Button).styles.display = "block"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.app.pop_screen()
