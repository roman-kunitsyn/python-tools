from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Select

from src.app.models.config import TranscribeConfig
from src.app.services.transcriber import SUPPORTED_FORMATS
from src.app.ui.widgets.action_buttons import ActionButtons
from src.app.ui.widgets.form_field import FormField
from src.app.ui.widgets.path_input import PathInput


class TranscribeForm(Vertical):
    def compose(self) -> ComposeResult:
        config = self.app.config
        audio_value = "" if config.audio_file is None else str(config.audio_file)
        output_value = "" if config.output_file is None else str(config.output_file)

        yield PathInput("Audio File", audio_value, id="audio-file")
        yield PathInput("Output File", output_value, id="output-file")
        yield FormField(
            "Format",
            Select(
                [(value, value) for value in sorted(SUPPORTED_FORMATS)],
                value=config.output_format,
                allow_blank=False,
                id="format",
            ),
        )
        yield PathInput("Model File", str(config.model_file), id="model-file")
        yield FormField(
            "Language", PathInput.input_widget(config.language, id="language")
        )
        yield ActionButtons()

    def build_config(self) -> TranscribeConfig:
        audio_file = self._path_value("#audio-file-input")
        output_file = self._path_value("#output-file-input")
        model_file = self._required_path_value("#model-file-input", "Model file")
        language = self.query_one("#language", PathInput.input_class).value.strip()
        output_format = str(self.query_one("#format", Select).value)

        return TranscribeConfig(
            audio_file=audio_file,
            output_file=output_file,
            output_format=output_format,
            model_file=model_file,
            language=language or "auto",
        )

    def _path_value(self, selector: str) -> Path | None:
        value = self.query_one(selector, PathInput.input_class).value.strip()
        if value == "":
            return None
        return Path(value).expanduser()

    def _required_path_value(self, selector: str, label: str) -> Path:
        value = self._path_value(selector)
        if value is None:
            raise ValueError(f"{label} is required")
        return value
