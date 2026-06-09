Personal Organizer
Terminal Life Manager App
Personal State Tracker

# Application domain

Containing:

```text
Schedule
User_State_Snapshot
Events
Reminders
Projects
Tasks
Goals
Wishes
Notes
```

```python
@dataclass
class Schedule:
    id: UUID
    title: str
    created_at: datetimez

@dataclass
class UserStateSnapshot:
    id: UUID
    emotion: str
    physical: str
    mental: str
    intuition: str
    comment: str | None
    created_at: datetimez

@dataclass
class Event:
    id: UUID
    title: str
    start: datetimez
    end: datetimez
    created_at: datetimez


@dataclass
class Reminder:
    id: UUID
    event_id: str | None
    minutes_before: int
    message: str
    created_at: datetimez


@dataclass
class Project:
    id: UUID
    title: str
    description: str
    created_at: datetimez

@dataclass
class Task:
    id: UUID
    title: str
    description: str
    project_id: UUID | None
    created_at: datetimez

@dataclass
class Goal:
    id: UUID
    title: str
    description: str
    created_at: datetimez

@dataclass
class Wish:
    id: UUID
    title: str
    description: str
    created_at: datetimez

@dataclass
class Note:
    id: UUID
    title: str
    content: str
    created_at: datetimez
```
