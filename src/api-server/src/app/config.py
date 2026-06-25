from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TOOLS_API_", extra="ignore")

    title: str = "Tools API"
    version: str = "0.1.0"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"
    default_meetings_dir: Path = Path.home() / "workspace" / "meetings"
    default_voice_notes_dir: Path = Path("logs") / "voice_notes"
    default_model_file: Path = Path.home() / "whisper" / "models" / "ggml-small.bin"
