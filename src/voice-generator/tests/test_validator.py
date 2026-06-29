from __future__ import annotations

from pathlib import Path
from unittest import TestCase

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.services.validator import validate_environment


class VoiceGeneratorValidatorTests(TestCase):
    def test_validate_environment_reports_missing_ffmpeg_path(self) -> None:
        config = VoiceGeneratorConfig(ffmpeg_path=Path("/definitely/not/ffmpeg"))

        report = validate_environment(config)

        self.assertFalse(report.ok)
        self.assertTrue(
            any(issue.check == "ffmpeg" for issue in report.issues),
            "expected ffmpeg validation issue",
        )
