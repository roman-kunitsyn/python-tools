from dataclasses import dataclass


@dataclass(frozen=True)
class AudioDevice:
    id: str
    name: str
    platform: str
