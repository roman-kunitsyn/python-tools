# Golden Standard Telegram Bot Guidelines

Document that every future bot follows.

Structure:

```
1. Philosophy
2. Architecture
3. Commands
4. Conversation Design
5. FSM Rules
6. Keyboards
7. Help System
8. Errors
9. Logging
10. Project Structure
11. Coding Standards
12. UX Standards
13. Security
14. Performance
15. Testing
```

---

# 1. Philosophy

The bot should feel like an application, not like a CLI.

Commands are only entry points.

Everything else is performed through:

- buttons
- forms
- FSM
- callbacks

Never require users to remember commands.

---

# 2. Global Commands

Every bot should have the same commands.

```
/start
/help
/menu
/settings
/cancel
/status
/about
```

Optional

```
/language
/debug
/version
```

---

## /start

Purpose

Initialize user.

Responsibilities

- register user
- create profile
- show welcome
- show available features

Example

```
👋 Welcome!

Available actions

🎤 Voice Notes
📄 Documents
⚙ Settings

Choose an option.
```

Buttons

```
Voice Notes
Documents
Settings
Help
```

---

## /help

Never print a wall of text.

Instead

```
Help

Choose a topic.
```

Buttons

```
Commands
How Voice Notes Work
FAQ
Support
```

Each page is small.

---

## /menu

Always returns user to main menu.

No matter current FSM.

---

## /cancel

Universal escape.

Always

- clear FSM
- rollback temporary state
- return to menu

---

## /settings

Examples

Language

Notifications

Timezone

Audio quality

Model

---

## /status

Current session

Current model

Queue

Statistics

---

## /about

Bot version

Developer

Links

---

# 3. Help System

Golden rule

Help must be contextual.

Instead of

```
Use /voice_note...
```

show

```
Voice Notes

1. Press Start

2. Send audio

3. Press Finish

Done.
```

---

Hierarchical help

```
Help

Voice Notes

Documents

Settings

FAQ

Support
```

---

# 4. Conversation Design

Every feature follows

```
Command

↓

Bot explains

↓

User sends input

↓

Bot validates

↓

Bot responds

↓

Buttons

↓

Repeat

↓

Finish
```

---

Never ask

```
What next?
```

Instead

Offer buttons.

---

# 5. FSM

Every feature owns its FSM.

Example

```
Idle

↓

WaitingAudio

↓

Processing

↓

WaitingDecision

↓

Finished
```

Never have giant FSM shared by everything.

---

# 6. Example Voice Notes

Flow

```
/voice_note

↓

Voice Note Session Started

↓

Waiting Audio

↓

User sends audio

↓

Save audio

↓

Transcribe

↓

Send transcription

↓

Buttons

➕ Add

✅ Finish

❌ Cancel
```

---

If Add

```
Waiting Audio
```

again.

---

If Finish

```
Merge notes

Generate summary

Save

Return menu
```

---

# 7. Message Design

Avoid walls of text.

Good

```
Voice note processed.

Duration
00:42

Language
English

Transcription

Lorem ipsum...

What next?
```

Buttons

```
➕ Add

✏ Rename

📝 Summary

✅ Finish

❌ Cancel
```

---

# 8. Buttons

Always prefer buttons.

Priority

```
InlineKeyboard
```

↓

```
ReplyKeyboard
```

↓

Commands

↓

Free typing

---

Inline buttons are preferable because

- easier UX
- deterministic
- FSM friendly

---

# 9. Project Structure

```
telegram_bot/

bot.py

config.py

handlers/

commands.py

voice.py

documents.py

settings.py

callbacks/

voice.py

settings.py

keyboards/

voice.py

main.py

states/

voice.py

middlewares/

services/

speech/

storage/

llm/

repositories/

models/

utils/

tests/
```

No business logic inside handlers.

Handlers only:

```
Receive Update

↓

Validate

↓

Call Service

↓

Build Response
```

---

# 10. Services

Example

```
VoiceService

SessionService

UserService

TranscriptionService

StorageService

LLMService
```

Handlers never call database directly.

---

# 11. Error Handling

Never expose Python exceptions.

Instead

```
❌ Failed to transcribe audio.

Please try again.
```

Log everything internally.

---

# 12. Logging

Every update gets

```
user_id

chat_id

message_id

session_id

FSM state

handler

execution time

errors
```

---

# 13. UX Standards

Always

Reply within 1 second if possible.

If processing takes longer

```
⏳ Processing audio...
```

Then edit the message with the result.

---

Never leave the user waiting silently.

---

# 14. Voice Notes UX

Recommended flow

```
/voice_note

↓

🎤 Voice Note Session Started

Send voice messages one by one.

When finished press

✅ Finish
```

User

(audio)

↓

Bot

```
Audio #1

Duration
00:21

Transcript

...

Buttons

➕ Add
📝 Summary
🗑 Delete
✅ Finish
❌ Cancel
```

User

Add

↓

(audio)

↓

Bot

```
Audio #2

Transcript

...
```

User

Finish

↓

Bot

```
Final Note

Files: 2

Duration: 03:17

Summary

...

Buttons

📄 Export Markdown
📄 Export PDF
🎤 New Session
🏠 Menu
```

---

# 15. Design Principles

- Keep commands minimal; use them only as entry points.
- Guide users with buttons instead of requiring memorized commands.
- Use one focused FSM per feature rather than a global state machine.
- Separate handlers, services, repositories, and UI components.
- Provide immediate feedback for every action, especially long-running tasks.
- Ensure `/menu` and `/cancel` always work from any state.
- Keep help contextual, concise, and accessible from every workflow.
- Design every interaction so the next action is obvious without typing.
