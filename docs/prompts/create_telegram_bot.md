you are
./docs/roles/TOOL_ENGINEER.md
I need to add new tools to my tool set.
I need to implement
src/voice-note/README.md

you are
./docs/roles/TOOL_ENGINEER.md

review project description
src/telegram-bot/README.md
it is just suggestion, need to update it according to our current project structure

need to implement
src/telegram-bot/README.md

docs/guidelines/TELEGRAM_BOT_GUIDELINE.md
docs/roles/profiles/python_telegram_engineer.json
docs/roles/TELEGRAM_ENGINEER.md

This is how I would write it for an AI coding agent (Codex, Claude Code, Cursor Agent, etc.). It focuses on **requirements**, **architecture**, **user flow**, and **acceptance criteria**, leaving implementation details to the engineer.

# Task: Implement Voice Note Feature

## Goal

Implement a production-ready **Voice Note** feature for a Telegram bot using **Python** and **Aiogram 3.x**.

The feature allows users to create a voice note consisting of one or more voice messages. Each message is saved, converted to wav, transcribed, and added to the current session. When the user finishes recording, all transcripts are combined into a single note.

The implementation must follow the project's Telegram Bot Guidelines and Clean Architecture principles.

---

# User Flow

```
User

↓

/voice_note

↓

Bot

Voice Note Session Started

Send one or more voice messages.

↓

User sends voice message

↓

Save audio

↓

Convert ogg to wav audio

↓

Transcribe

↓

Return transcription

↓

Buttons

➕ Add More
✅ Finish
❌ Cancel
```

If the user selects **Add More**, the bot waits for another voice message.

If the user selects **Finish**, the session is completed.

---

# Conversation Flow

```
Idle

↓

Voice Session Started

↓

Waiting for Voice

↓

Receive Voice

↓

Save Audio

↓

Convert Audio to wav

↓

Transcribe

↓

Display Result

↓

Waiting Decision

 ├── Add More
 │      ↓
 │ Waiting for Voice
 │
 ├── Finish
 │      ↓
 │ Merge Notes
 │ Generate Summary (optional)
 │ Save Session
 │ Return to Menu
 │
 └── Cancel
        ↓
Delete Temporary Data
Return to Menu
```

---

# Functional Requirements

## Start Session

Command

```
/voice_note
```

The bot should

- create a new voice session
- generate a unique session ID
- initialize FSM state
- display recording instructions

Example

```
🎤 Voice Note Session Started

Send one or more voice messages.

When finished press:

✅ Finish
```

Buttons

```
➕ Add More (disabled until first audio)
✅ Finish
❌ Cancel
```

---

## Receive Voice

Supported messages

- Telegram Voice
- Telegram Audio (optional)

For every received audio

- download file
- save locally
- assign sequential number
- store metadata
- enqueue transcription

---

## Transcription

The transcription service should return

- transcript
- detected language (optional)
- duration

After transcription

Display

```
Voice #2

Duration: 00:37

Transcript

Lorem ipsum...

```

Buttons

```
➕ Add More

✅ Finish

❌ Cancel
```

---

## Add More

When pressed

Return FSM to

```
WaitingVoice
```

The next voice message should be appended to the current session.

---

## Finish

When Finish is selected

The bot should

- finalize session
- merge transcripts
- calculate statistics
- save session
- clear FSM

Optional

Generate

- AI summary
- title
- keywords

Display

```
Voice Note Saved

Voices: 4

Duration: 07:13

Characters: 3854
```

Buttons

```
📄 Show Note

📝 Summary

🎤 New Voice Note

🏠 Menu
```

---

## Cancel

When Cancel is selected

The bot should

- clear FSM
- remove temporary files
- discard unsaved session
- return to main menu

---

# FSM States

```
Idle

VoiceNoteStarted

WaitingVoice

ProcessingVoice

WaitingDecision

Finished
```

Each feature must own its own FSM.

---

# Storage

Store every uploaded voice separately.

Example

```
storage/

voice_notes/

session_001/

voice_001.ogg

voice_002.ogg

voice_003.ogg

transcript.md

metadata.json
```

---

# Metadata

Example

```json
{
  "session_id": "...",
  "user_id": "...",
  "created_at": "...",
  "voices": [
    {
      "index": 1,
      "duration": 32,
      "file": "voice001.ogg",
      "transcript": "..."
    }
  ]
}
```

---

# Project Structure

```
handlers/

voice_note.py

callbacks/

voice_note.py

states/

voice_note.py

services/

voice_note_service.py

transcription_service.py

storage_service.py

repositories/

voice_note_repository.py

keyboards/

voice_note.py
```

---

# Services

Implement

## VoiceNoteService

Responsibilities

- create session
- append voice
- finish session
- cancel session
- merge transcripts

---

## TranscriptionService

Responsibilities

- transcribe audio
- detect language
- return transcript

---

## StorageService

Responsibilities

- save audio
- load audio
- remove temporary files

---

# Logging

Log

- session started
- voice received
- transcription completed
- finish
- cancel
- processing time
- errors

Every log should include

- user_id
- chat_id
- session_id

---

# Error Handling

Possible failures

- invalid file
- download failed
- transcription failed
- storage unavailable

The user should receive friendly messages.

Example

```
❌ Unable to transcribe this recording.

Please try again.
```

Never expose stack traces.

---

# Acceptance Criteria

- `/voice_note` starts a new session.
- User can upload multiple voice messages.
- Every voice is saved locally.
- Every voice is transcribed automatically.
- User can continue adding recordings.
- User can finish the session.
- Final transcript contains all recordings in chronological order.
- Temporary files are cleaned after cancellation.
- FSM is reset after finish or cancel.
- All business logic resides in services.
- Handlers remain thin.
- Feature is fully asynchronous.
- Structured logging is implemented.
- Code follows project architecture and coding standards.

---

# Future Extensions

The implementation should be designed to support future features without major refactoring.

Possible extensions include:

- AI-generated summaries
- automatic titles
- note tagging
- keyword extraction
- Markdown export
- PDF export
- Obsidian export
- synchronization with external note systems
- searchable note history
- vector embeddings and semantic search
- speaker diarization
- multilingual transcription
- cloud storage backends
- background processing queues
- transcription progress updates

This specification is intentionally implementation-agnostic: it defines **what** the feature must do, while leaving **how** to implement it (storage backend, transcription engine, dependency injection, etc.) to the engineer following your project architecture.
