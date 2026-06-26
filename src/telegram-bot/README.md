# Telegram Bot

## Project Overview

`telegram-bot` is a Telegram adapter for the Python tools workspace.
It uses `aiogram` to receive updates, routes them through a thin service layer,
and reuses the existing `voice-note` transcription pipeline for audio input.

The bot currently focuses on one workflow:

- receive a voice message or audio file
- download it locally
- transcribe it with the same Whisper-based logic used by `voice-note`
- send the transcript back to Telegram

## Requirements

- Python 3.14 or newer
- `uv`
- `aiogram`
- `pydantic`
- `pydantic-settings`

Runtime dependencies:

- `whisper-cli` on `PATH`
- a Whisper model file, by default `small`
- a Telegram bot token

## Start

Show help:

```bash
uv run python src/telegram-bot/telegram-bot.py --help
```

Start the bot with an environment token:

```bash
TELEGRAM_BOT_TOKEN=123456:token uv run python src/telegram-bot/telegram-bot.py
```

Override the token and Whisper settings on the command line:

```bash
uv run python src/telegram-bot/telegram-bot.py \
  --token 123456:token \
  --model small \
  --language auto
```

Enable command logging from `whisper-cli`:

```bash
uv run python src/telegram-bot/telegram-bot.py \
  --token 123456:token \
  --verbose
```

## Bot Commands

### `/start`

Shows the basic usage message and explains that the bot transcribes voice and
audio messages.

### `/voice-note`

Marks the next interaction as a voice-note workflow and prompts the user to
send a voice message or audio file.

## Message Handling

The bot accepts:

- Telegram voice messages
- Telegram audio files

For each message it:

1. creates a session folder under `logs/voice_notes`
2. downloads the file into that session's `audio/` folder
3. converts the downloaded audio to `wav`
4. runs Whisper transcription through the shared `voice-note` transcription
   wrapper and writes `transcribe.txt`
5. replies with the transcript

If the transcript is long, the reply is split into smaller chunks.

## Project Structure

```text
src/telegram-bot/
├── telegram-bot.py
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDELINE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── reports/
├── tests/
└── telegram_bot/
    ├── bot.py
    ├── bootstrap.py
    ├── config.py
    ├── handlers/
    ├── main.py
    ├── models.py
    └── services/
```

`telegram-bot.py` is only the script entry point. Application behavior lives in
`telegram_bot`.

Each Telegram note is stored in a folder like:

```text
logs/voice_notes/voice_note_{YYYY_MM_DD-HH_MM_SS}_{chat_id}_{message_id}/
├── audio/
│   ├── voice_{message_id}.ogg
│   └── voice_{message_id}.wav
└── transcribe.txt
```

## Documentation

- [Development Guideline](docs/DEVELOPMENT_GUIDELINE.md)
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [Reports](docs/reports/)

Shared workspace docs:

- [Architecture Guideline](../../docs/guidelines/ARCHITECTURE_GUIDELINE.md)
- [Implementation Guideline](../../docs/guidelines/IMPLEMENTATION_GUIDELINE.md)
- [Tool Engineer](../../docs/roles/TOOL_ENGINEER.md)
- [voice-note README](../voice-note/README.md)
