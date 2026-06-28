from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from browser_automation.models import RecorderResult
from browser_automation.utils.paths import ensure_parent, page_path_for_url


@dataclass(slots=True)
class BrowserRecorder:
    browser: str = "chromium"
    target: str = "python"

    def record(self, url: str | None, output_path: Path) -> RecorderResult:
        ensure_parent(output_path)
        command = [
            "playwright",
            "codegen",
            "--browser",
            self.browser,
            "--target",
            self.target,
            "--output",
            str(output_path),
        ]
        if url is not None:
            command.append(url)

        completed = subprocess.run(command, check=False)
        return RecorderResult(scenario_path=output_path, output_path=output_path, exit_code=completed.returncode)


def default_recording_path(url: str | None, output_dir: Path) -> Path:
    if url is None:
        return output_dir / "recorded_scenario.py"
    return page_path_for_url(url, output_dir, ".py")
