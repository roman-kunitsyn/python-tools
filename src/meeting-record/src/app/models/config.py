from dataclasses import dataclass
from pathlib import Path


DEFAULT_MEETINGS_DIR = Path.home() / "workspace" / "meetings"
DEFAULT_DEVICE_NAME = "Aggregate Device"


@dataclass
class RecordConfig:
    meetings_dir: Path
    stamp: str
    device_name: str
    timestamp: str | None = None
