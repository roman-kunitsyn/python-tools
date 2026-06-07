from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical

from src.app.models.config import RecordConfig
from src.app.ui.widgets.action_buttons import ActionButtons
from src.app.ui.widgets.text_input import TextInput


class RecordForm(Vertical):
    def compose(self) -> ComposeResult:
        config = self.app.config
        timestamp_value = "" if config.timestamp is None else config.timestamp

        yield TextInput("Stamp", config.stamp, placeholder="team-sync", id="stamp")
        yield TextInput(
            "Meetings Directory",
            str(config.meetings_dir),
            placeholder="~/workspace/meetings",
            id="meetings-dir",
        )
        yield TextInput(
            "Device Name",
            config.device_name,
            placeholder="Aggregate Device",
            id="device-name",
        )
        yield TextInput(
            "Timestamp",
            timestamp_value,
            placeholder="YYYY_MM_DD-HH_MM_SS",
            id="timestamp",
        )
        yield ActionButtons()

    def build_config(self) -> RecordConfig:
        meetings_dir = self._required_value("#meetings-dir-input", "Meetings Directory")
        device_name = self._required_value("#device-name-input", "Device Name")
        stamp = self._value("#stamp-input")
        timestamp = self._value("#timestamp-input") or None

        return RecordConfig(
            meetings_dir=Path(meetings_dir).expanduser(),
            stamp=stamp,
            device_name=device_name,
            timestamp=timestamp,
        )

    def _value(self, selector: str) -> str:
        return self.query_one(selector, TextInput.input_class).value.strip()

    def _required_value(self, selector: str, label: str) -> str:
        value = self._value(selector)
        if value == "":
            raise ValueError(f"{label} is required")
        return value
