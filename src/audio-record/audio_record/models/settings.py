from dataclasses import dataclass
from pathlib import Path


DEFAULT_FORMAT = "wav"


@dataclass(frozen=True)
class RecordingSettings:
    output_file: Path | None = None
    device: str | None = None
    duration: float | None = None
    sample_rate: int = 16000
    channels: int = 1
    output_format: str = DEFAULT_FORMAT

    def validate(self) -> None:
        if self.duration is not None and self.duration <= 0:
            raise ValueError("duration must be greater than zero")

        if self.sample_rate <= 0:
            raise ValueError("sample-rate must be greater than zero")

        if self.channels not in (1, 2):
            raise ValueError("channels must be 1 or 2")
