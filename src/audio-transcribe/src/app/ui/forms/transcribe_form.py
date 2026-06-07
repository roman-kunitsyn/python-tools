from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Select

from src.app.models.config import TranscribeConfig
from src.app.services.models import list_model_files
from src.app.services.transcriber import SUPPORTED_FORMATS
from src.app.ui.widgets.action_buttons import ActionButtons
from src.app.ui.widgets.form_field import FormField
from src.app.ui.widgets.path_input import PathInput


class TranscribeForm(Vertical):
    def compose(self) -> ComposeResult:
        config = self.app.config
        audio_value = "" if config.audio_file is None else str(config.audio_file)
        output_value = "" if config.output_file is None else str(config.output_file)
        model_options = self._model_options()
        model_value = self._model_value(config.model_file, model_options)

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
        yield FormField(
            "Model File",
            Select(
                model_options,
                value=model_value,
                allow_blank=False,
                disabled=model_options[0][1] == "",
                id="model-file",
            ),
        )
        yield FormField(
            "Language", PathInput.input_widget(config.language, id="language")
        )
        yield ActionButtons()

    def build_config(self) -> TranscribeConfig:
        audio_file = self._path_value("#audio-file-input")
        output_file = self._path_value("#output-file-input")
        model_file = self._selected_model_file()
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

    def _model_options(self) -> list[tuple[str, str]]:
        model_files = list_model_files()

        if not model_files:
            return [("No models found in ~/whisper/models", "")]

        return [(path.name, str(path)) for path in sorted(model_files)]

    def _model_value(
        self,
        selected_model: Path,
        model_options: list[tuple[str, str]],
    ) -> str:
        option_values = {value for _, value in model_options}
        selected_model_value = str(selected_model)

        if selected_model_value in option_values:
            return selected_model_value

        return model_options[0][1]

    def _selected_model_file(self) -> Path:
        selected_model = str(self.query_one("#model-file", Select).value)
        if selected_model == "":
            raise ValueError("No model files found in ~/whisper/models")
        return Path(selected_model).expanduser()
