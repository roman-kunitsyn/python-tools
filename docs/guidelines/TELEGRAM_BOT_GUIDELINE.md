# Telegram Bot Guideline

Use this guideline for Telegram bots in this repository, especially bots built
with Python and Aiogram 3.x.

The goal is a reusable app shape:

```text
Telegram update
handler
service layer
shared models and config
storage or external tool wrapper
response
```

## Core Principle

Keep the bot focused on one user-visible responsibility.

Good scope:

```text
Telegram voice messages -> saved audio -> transcript -> combined note
```

Good scope:

```text
Telegram command -> external tool workflow -> structured response
```

Avoid mixing unrelated responsibilities in one bot. Voice notes, document
processing, task extraction, and admin workflows should be separate features or
separate services with clear boundaries.

## Conversation Design

Design features as short, explicit flows.

Recommended flow:

```text
Command
  -> bot explains the next step
  -> user sends input
  -> bot validates input
  -> bot processes in a service
  -> bot responds with a clear next action
```

If a feature has more than one step, give it its own FSM.

## Standard Structure

Use this structure for Telegram bot projects in this repo:

```text
telegram-bot/
├── telegram-bot.py
├── README.md
├── docs/
│   ├── DEVELOPMENT_GUIDELINE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── reports/
└── telegram_bot/
    ├── __init__.py
    ├── main.py
    ├── bot.py
    ├── config.py
    ├── handlers/
    ├── services/
    ├── models.py
    └── bootstrap.py
```

Keep handlers thin. Put behavior in services. Keep storage and conversion logic
out of message handlers.

## Commands

Commands are entry points only.

Recommended baseline:

```text
/start
/help
/menu
/cancel
```

Feature-specific commands are allowed when they clearly start a workflow, such
as `/voice-note`.

## Voice Note Flow

For voice-note style workflows, keep the flow explicit:

```text
/voice-note
  -> start session
  -> wait for voice/audio
  -> download file
  -> convert to wav
  -> transcribe
  -> show transcript
  -> add more, finish, or cancel
```

Store each uploaded message separately. If a feature later merges multiple
messages into one result, do that in a service after the individual items are
stored.

## FSM Rules

Use a separate FSM per feature.

Useful states:

```text
Idle
Started
WaitingInput
ProcessingInput
WaitingDecision
Finished
```

Rules:

- handlers should transition state
- services should own business rules
- cancellation should always clear temporary state
- finish should always reset the FSM

## Services

Implement service classes for core workflows.

Example responsibilities:

- create session
- append item
- finish session
- cancel session
- merge transcripts
- normalize media to wav
- call transcription engines

Services should be importable and testable without launching Telegram.

## Storage

Store uploaded files in a predictable workspace folder.

Recommended pattern:

```text
logs/voice_notes/
  voice_note_{timestamp}_{chat_id}_{message_id}/
    audio/
      voice_{message_id}.ogg
      voice_{message_id}.wav
    transcribe.txt
    metadata.json
```

Keep storage decisions in services or storage helpers, not handlers.

## Logging

Log the important lifecycle events:

- session started
- message received
- file downloaded
- conversion completed
- transcription completed
- finish
- cancel
- errors

Every log record should include:

- `user_id`
- `chat_id`
- `session_id`

## Error Handling

Possible failures:

- invalid file type
- download failure
- conversion failure
- transcription failure
- storage failure

Users should receive friendly messages. Do not expose stack traces.

Example:

```text
❌ Unable to transcribe this recording.

Please try again.
```

## Project Structure Rules

Use these layers:

- `handlers/` for Telegram updates and command routing
- `services/` for workflow logic
- `models.py` or `models/` for shared data objects
- `config.py` for environment-driven settings
- `bootstrap.py` only when import path bootstrapping is unavoidable

Do not put external command construction, file conversion, or transcription
logic in handlers.

## Testing

Test business logic separately from Telegram transport.

Recommended tests:

- conversation state
- source parsing
- service workflow
- storage path generation
- transcription wrapper calls
- error mapping

Use fakes instead of real Telegram or external tool calls in core tests.

## Coding Standards

- Use Python 3.14 or newer unless the repo says otherwise.
- Use Aiogram 3.x.
- Prefer asynchronous APIs.
- Keep modules small and cohesive.
- Use `Path` for filesystem values.
- Use subprocess command lists, not shell strings.
- Prefer dependency injection for services and wrappers.

## UX Standards

- Every user action should lead to a clear next action.
- Use buttons when they reduce ambiguity.
- Keep messages short and readable.
- Confirm when work starts and when it finishes.
- Provide a cancel path for every multi-step flow.

## Security

- Do not hardcode secrets.
- Load tokens and environment values from configuration.
- Do not expose internal errors to the user.
- Validate uploaded file types and sizes before processing.

## Performance

- Keep handlers non-blocking.
- Move blocking conversion or transcription work to services or background
  tasks.
- Avoid unnecessary duplicate downloads or conversions.
- Keep session cleanup deterministic.

## Acceptance Standard

A Telegram bot feature is complete when:

- the documented command starts the workflow
- users can complete the intended conversation flow
- uploaded files are saved in the project workspace
- media is converted or normalized as required
- transcripts or outputs are produced in order
- cancel and finish both clear temporary state
- handlers stay thin
- services own the business logic
- tests cover the core workflow
- the README and implementation plan reflect the real behavior

