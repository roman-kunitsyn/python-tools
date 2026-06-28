class BrowserAutomationError(RuntimeError):
    """Base error for browser automation failures."""


class ScenarioNotFoundError(BrowserAutomationError):
    """Raised when a scenario file does not define an entry callable."""
