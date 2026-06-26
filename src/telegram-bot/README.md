# Telegram Bot

`telegram-bot` is the Aiogram 3 adapter for the Python tools workspace. It
implements the voice-note workflow described in the Telegram bot guidelines and
keeps business logic in services while handlers stay thin.

## What It Does

- `/start` shows the main menu
- `/help` shows command help and current session guidance
- `/voice_note` starts a new voice-note session
- Users can send multiple voice messages or audio files
- Each upload is saved locally, converted to `wav`, and transcribed
- `Add More`, `Finish`, and `Cancel` are exposed as inline actions
- Finished sessions keep a chronological transcript and metadata file
- Cancelled sessions remove temporary data

## Runtime Requirements

- Python 3.14 or newer
- `uv`
- `aiogram`
- `pydantic`
- `pydantic-settings`
- `whisper-cli` on `PATH`
- `ffmpeg` on `PATH`
- a Telegram bot token

## Start

Show help:

```bash
uv run python src/telegram-bot/telegram-bot.py --help
```

Start the bot:

```bash
TELEGRAM_BOT_TOKEN=123456:token uv run python src/telegram-bot/telegram-bot.py
```

Override Whisper settings:

```bash
uv run python src/telegram-bot/telegram-bot.py \
  --token 123456:token \
  --model small \
  --language auto
```

Enable Whisper command logging:

```bash
uv run python src/telegram-bot/telegram-bot.py \
  --token 123456:token \
  --verbose
```

## Voice Note Flow

1. User sends `/voice_note`
2. Bot creates a session under `logs/voice_notes`
3. User sends one or more voice messages or audio files
4. Each upload is stored under the session folder and converted to `wav`
5. Whisper transcription runs automatically
6. Bot returns the transcript and shows `Add More`, `Finish`, `Cancel`
7. `Finish` finalizes the session and keeps the transcript
8. `Cancel` removes the session directory and clears temporary state

## Session Layout

Each session is stored locally in its own folder:

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

`metadata.json` tracks session metadata and per-voice details. `transcript.md`
contains the merged transcript in chronological order.

## Project Structure

```text
src/telegram-bot/
├── telegram-bot.py
├── README.md
├── docs/
├── tests/
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

## Key Modules

- `telegram_bot/main.py` bootstraps the bot process
- `telegram_bot/bot.py` builds the dispatcher and router tree
- `telegram_bot/services/voice_note.py` owns session orchestration
- `telegram_bot/services/storage_service.py` owns local session storage
- `telegram_bot/services/transcription.py` wraps `whisper-cli`
- `telegram_bot/handlers/*` keep Telegram handlers thin

## Documentation

- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [Reports](docs/reports/)

Shared workspace docs:

- [Telegram Bot Guideline](../../docs/guidelines/TELEGRAM_BOT_GUIDELINE.md)
- [Telegram Engineer](../../docs/roles/TELEGRAM_ENGINEER.md)
- [Tool Engineer](../../docs/roles/TOOL_ENGINEER.md)
- [voice-note README](../voice-note/README.md)
