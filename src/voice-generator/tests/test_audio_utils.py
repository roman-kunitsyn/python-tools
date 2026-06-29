from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from voice_generator.utils.audio import resolve_output_path


class OutputPathTests(TestCase):
    def test_resolve_output_path_uses_timestamped_logs_directory(self) -> None:
        with patch("voice_generator.utils.audio.build_timestamp", return_value="2026_06_30-05_55_00"), patch(
            "voice_generator.utils.audio.Path.cwd",
            return_value=Path("/workspace"),
        ):
            resolved = resolve_output_path(
                None,
                provider="macos",
                voice="Samantha",
                output_format="wav",
            )

        self.assertEqual(
            resolved,
            Path("/workspace/logs/voice-generator/2026_06_30-05_55_00.wav"),
        )
