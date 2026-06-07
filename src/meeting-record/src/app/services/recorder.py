import json
from datetime import datetime
from pathlib import Path

from src.app.models.config import RecordConfig
from src.app.services.ffmpeg import FfmpegWrapper
from src.app.services.models import RecordingResult


TIMESTAMP_FORMAT = "%Y_%m_%d-%H_%M_%S"


def build_timestamp() -> str:
    return datetime.now().strftime(TIMESTAMP_FORMAT)


def validate_timestamp(timestamp: str) -> None:
    try:
        datetime.strptime(timestamp, TIMESTAMP_FORMAT)
    except ValueError as error:
        raise ValueError(
            f"Timestamp must match format {TIMESTAMP_FORMAT}: {timestamp}"
        ) from error


def build_meeting_dir(meetings_dir: Path, timestamp: str) -> Path:
    return meetings_dir / f"meeting-{timestamp}"


def build_audio_file(meeting_dir: Path, timestamp: str) -> Path:
    return meeting_dir / f"meeting-core-{timestamp}.wav"


def write_metadata(metadata_file: Path, stamp: str, timestamp: str) -> None:
    payload = {
        "stamp": stamp,
        "timestamp": timestamp,
    }
    metadata_file.write_text(json.dumps(payload, indent=2) + "\n")


class MeetingRecordService:
    def __init__(
        self,
        ffmpeg: FfmpegWrapper | None = None,
        verbose: bool = False,
    ) -> None:
        self.ffmpeg = ffmpeg or FfmpegWrapper()
        self.verbose = verbose

    def record(self, config: RecordConfig) -> RecordingResult:
        timestamp = config.timestamp or build_timestamp()
        validate_timestamp(timestamp)

        meeting_dir = build_meeting_dir(config.meetings_dir, timestamp)
        audio_file = build_audio_file(meeting_dir, timestamp)
        metadata_file = meeting_dir / "metadata.json"
        device_code = self.ffmpeg.find_audio_device_code(config.device_name)

        meeting_dir.mkdir(parents=True, exist_ok=False)
        write_metadata(
            metadata_file=metadata_file,
            stamp=config.stamp,
            timestamp=timestamp,
        )

        self.ffmpeg.record_audio(
            device_code=device_code,
            output_file=audio_file,
            verbose=self.verbose,
        )

        return RecordingResult(
            meeting_dir=meeting_dir,
            audio_file=audio_file,
            metadata_file=metadata_file,
            timestamp=timestamp,
        )
