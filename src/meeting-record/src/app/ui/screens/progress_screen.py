import subprocess

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label, LoadingIndicator, Static

from src.app.models.config import RecordConfig
from src.app.services.recorder import MeetingRecordService
from src.app.ui.widgets.footer_bar import FooterBar


class ProgressScreen(Screen):
    def __init__(self, config: RecordConfig) -> None:
        super().__init__()
        self.config = config
        self.service = MeetingRecordService()
        self.stop_requested = False

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Recording...", id="title"),
            LoadingIndicator(id="loading"),
            Static("Recording is active. Use Stop to finish the session.", id="status"),
            Button("Stop", variant="error", id="stop"),
            Button("Back", id="back"),
            id="content",
        )
        yield FooterBar()

    def on_mount(self) -> None:
        self.query_one("#back", Button).styles.display = "none"
        self.run_worker(self._run_recording, thread=True)

    def _run_recording(self) -> None:
        try:
            result = self.service.record(self.config)
        except ValueError as error:
            self.app.call_from_thread(self._show_result, f"Validation error: {error}")
        except FileExistsError as error:
            self.app.call_from_thread(
                self._show_result,
                f"Output already exists: {error.filename}",
            )
        except FileNotFoundError as error:
            self.app.call_from_thread(self._show_result, f"ffmpeg failed: {error}")
        except subprocess.CalledProcessError as error:
            self.app.call_from_thread(
                self._show_result,
                f"ffmpeg failed with exit code {error.returncode}.",
            )
        else:
            prefix = "Recording stopped." if self.stop_requested else "Recording saved."
            self.app.call_from_thread(
                self._show_result,
                (
                    f"{prefix}\n"
                    f"Meeting directory: {result.meeting_dir}\n"
                    f"Audio file: {result.audio_file}\n"
                    f"Metadata file: {result.metadata_file}"
                ),
            )

    def _show_result(self, message: str) -> None:
        self.query_one("#title", Label).update("Finished")
        self.query_one("#loading", LoadingIndicator).styles.display = "none"
        self.query_one("#status", Static).update(message)
        self.query_one("#stop", Button).styles.display = "none"
        self.query_one("#back", Button).styles.display = "block"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "stop":
            self.stop_requested = True
            self.query_one("#status", Static).update("Stopping recording...")
            self.query_one("#stop", Button).disabled = True
            self.service.stop_recording()
            return

        if event.button.id == "back":
            self.app.pop_screen()
