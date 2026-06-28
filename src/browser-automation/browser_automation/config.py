from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class Viewport(BaseModel):
    width: int = 1440
    height: int = 900


class BrowserAutomationConfig(BaseModel):
    headless: bool = True
    timeout: int = 30_000
    browser: Literal["chromium", "firefox", "webkit"] = "chromium"
    viewport: Viewport = Field(default_factory=Viewport)
    slow_mo: int | None = None
    output_dir: Path = Path("browser-output")
    config_file: Path | None = None

    @classmethod
    def from_file(cls, config_file: Path) -> "BrowserAutomationConfig":
        return cls.model_validate_json(config_file.read_text())

    @classmethod
    def from_args(
        cls,
        *,
        config_file: Path | None = None,
        headless: bool | None = None,
        timeout: int | None = None,
        browser: str | None = None,
        viewport_width: int | None = None,
        viewport_height: int | None = None,
        slow_mo: int | None = None,
        output_dir: Path | None = None,
    ) -> "BrowserAutomationConfig":
        data: dict[str, object] = {}

        if config_file is not None:
            data.update(cls.from_file(config_file).model_dump())

        if headless is not None:
            data["headless"] = headless
        if timeout is not None:
            data["timeout"] = timeout
        if browser is not None:
            data["browser"] = browser
        if output_dir is not None:
            data["output_dir"] = output_dir
        if slow_mo is not None:
            data["slow_mo"] = slow_mo

        viewport = dict(data.get("viewport", {}))
        if viewport_width is not None:
            viewport["width"] = viewport_width
        if viewport_height is not None:
            viewport["height"] = viewport_height
        if viewport:
            data["viewport"] = viewport

        if config_file is not None:
            data["config_file"] = config_file

        return cls.model_validate(data)
