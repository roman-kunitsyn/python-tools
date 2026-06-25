# Telegram Bot Implementation Plan

## Module Purpose

`telegram-bot` provides a Telegram interface around the workspace tools,
starting with voice-note transcription.

The bot should remain an adapter layer:

- Telegram handlers parse incoming updates.
- Services manage conversation state and transcription calls.
- The existing `voice-note` tool performs the Whisper-based transcription.

## Current Structure

```text
src/telegram-bot/
├── telegram-bot.py
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDELINE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── reports/
└── telegram_bot/
    ├── bot.py
    ├── bootstrap.py
    ├── config.py
    ├── handlers/
    ├── main.py
    ├── models.py
    └── services/
```

Current layer ownership:

- `telegram-bot.py`: thin script entry point.
- `telegram_bot/main.py`: CLI parsing, settings construction, and polling
  startup.
- `telegram_bot/config.py`: bot settings.
- `telegram_bot/models.py`: shared data models.
- `telegram_bot/services/conversation.py`: in-memory voice-note session state.
- `telegram_bot/services/transcription.py`: Whisper transcription wrapper.
- `telegram_bot/services/voice_note.py`: message download, transcription, and
  response formatting.
- `telegram_bot/handlers/`: command and media message handlers.

## Implemented

- Thin launcher script.
- `aiogram` polling application.
- `/start` command.
- `/voice-note` command.
- voice and audio message transcription.
- in-memory conversation state for voice-note mode.
- reply formatting and chunking helpers.
- module-local development guideline and implementation plan.
- initial unit tests.

## Known Gaps

- Bot token is required at runtime and must come from `--token` or
  `TELEGRAM_BOT_TOKEN`.
- Conversation state is memory-only.
- No persistence for transcripts or downloads.
- No Telegram integration tests against a real bot account.
- No rate limiting or admin access control.

## Current Acceptance State

Completed:

- Runnable bot entry point.
- Voice-message transcription flow.
- Handler/service split.
- Initial tests and documentation.

Partial:

- Error mapping is intentionally simple and may need refinement.
- Large transcript delivery may need smarter chunking later.

Not started:

- Persistent session storage.
- Webhook deployment.
- Rich command menu or inline keyboard flows.

## Next Small Parts

### Part 2: Add Admin and Status Commands

Goal:

Give the bot a small operational surface for checking status and resetting
conversation state.

Deliverables:

- `/status`
- `/cancel`
- `/help`

### Part 3: Persist Sessions

Goal:

Store active voice-note session state outside process memory.

Deliverables:

- file-backed or database-backed session state
- restart-safe behavior

### Part 4: Integration Checks

Goal:

Verify the bot startup path and message formatting against the real runtime
dependencies.

Deliverables:

- startup smoke tests
- guarded Telegram integration tests
- voice-note transcription regression checks

## Documentation Rules For This Module

When implementation changes:

1. Update this plan to reflect the real module state.
2. Update `README.md` if user-facing behavior changed.
3. Add a report under `docs/reports/`.
4. Keep handlers thin and route behavior through services.
