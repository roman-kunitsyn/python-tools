# Telegram Bot Implementation Plan

## Module Purpose

`telegram-bot` provides a Telegram interface for the workspace voice-note
feature. It uses Aiogram 3, a thin handler layer, and service classes that own
session storage, transcription, and cleanup.

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
    ├── keyboards/
    ├── main.py
    ├── models.py
    ├── services/
    └── states/
```

## Current Ownership

- `telegram-bot.py`: thin script entry point.
- `telegram_bot/main.py`: CLI parsing, settings construction, and polling startup.
- `telegram_bot/config.py`: bot settings, including `logs/voice_notes`.
- `telegram_bot/models.py`: session and entry models.
- `telegram_bot/services/conversation.py`: in-memory active session store.
- `telegram_bot/services/storage_service.py`: session directory lifecycle, local audio storage, WAV conversion, transcript and metadata persistence.
- `telegram_bot/services/transcription.py`: async wrapper around `whisper-cli`.
- `telegram_bot/services/voice_note.py`: session orchestration and structured logging.
- `telegram_bot/handlers/`: command, callback, and media handlers.
- `telegram_bot/states/voice_note.py`: FSM for the voice-note flow.
- `telegram_bot/keyboards/`: inline keyboards for the main menu and voice-note session.

## Implemented Flow

- `/start` shows the menu.
- `/help` shows command help.
- `/voice_note` starts a new session.
- The user can send multiple voice or audio messages.
- Each upload is stored locally, converted to `wav`, and transcribed.
- The bot returns the transcript and offers `Add More`, `Finish`, and `Cancel`.
- `Finish` merges transcript output, finalizes metadata, and clears the FSM state.
- `Cancel` removes the session directory and clears the FSM state.

## Current Storage Layout

```text
logs/voice_notes/
└── voice_note_YYYY_MM_DD-HH_MM_SS_<session_id>/
    ├── audio/
    │   ├── voice_001.ogg
    │   ├── voice_001.wav
    │   ├── voice_002.ogg
    │   └── voice_002.wav
    ├── metadata.json
    └── transcript.md
```

## Verified Guarantees

- handlers remain thin
- all business logic lives in services
- transcription runs asynchronously
- temp files are removed on cancel
- session transcript order matches arrival order
- logging includes `chat_id`, `user_id`, and `session_id`

## Remaining Risks

- `conversation_store` is still in memory, so active sessions do not survive a restart
- Telegram delivery limits may still require chunking for long transcripts
- no live Telegram integration test is present yet

## Next Small Parts

1. Add persistent session storage if restart safety becomes required.
2. Add command tests around the inline-button callbacks if the flow changes again.
3. Add a live-bot smoke test or webhook deployment path if needed.
