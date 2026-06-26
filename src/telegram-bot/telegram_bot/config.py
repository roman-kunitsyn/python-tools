from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TELEGRAM_BOT_", extra="ignore")

    token: str = Field(min_length=1)
    model: str = "small"
    language: str = "auto"
    verbose: bool = False
    log_file: Path | None = None
    reply_chunk_size: int = 3500
