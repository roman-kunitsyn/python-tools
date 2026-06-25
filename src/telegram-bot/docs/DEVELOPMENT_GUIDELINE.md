# Telegram Bot Development Guideline

This module adapts Telegram updates into workspace tool actions.

Keep these rules in mind:

- handlers should stay thin
- the voice-note tool remains the source of truth for transcription behavior
- blocking transcription work should run outside the event loop thread
- command parsing belongs in handlers, not service code
- document every implementation step with a plan update and a report

Shared guidance:

- [Architecture Guideline](../../../docs/guidelines/ARCHITECTURE_GUIDELINE.md)
- [Implementation Guideline](../../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md)
- [Tool Engineer](../../../docs/roles/TOOL_ENGINEER.md)
