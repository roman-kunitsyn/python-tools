class VoiceGeneratorError(Exception):
    exit_code = 2

    def __init__(self, message: str, *, exit_code: int | None = None) -> None:
        super().__init__(message)
        if exit_code is not None:
            self.exit_code = exit_code


class ValidationError(VoiceGeneratorError):
    exit_code = 1


class ProviderUnavailableError(VoiceGeneratorError):
    exit_code = 3


class MissingModelError(VoiceGeneratorError):
    exit_code = 3


class AudioGenerationError(VoiceGeneratorError):
    exit_code = 2


class FeatureNotImplementedError(VoiceGeneratorError):
    exit_code = 2
