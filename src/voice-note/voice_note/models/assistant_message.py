from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class AssistantMessage:
    message_id: str
    role: str
    prompt: str
    response: str
    created_at: datetime
    source_audio: Path | None = None
    response_state: str = "draft"
