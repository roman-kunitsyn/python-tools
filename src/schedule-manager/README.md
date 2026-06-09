```sh
schedule-engine/
├── config
│   ├── app.yaml
│   └── notifications.yaml
│
├── schedules
│   ├── university.yaml
│   ├── work.yaml
│   └── gym.yaml
│
├── sounds
│   ├── chime.mp3
│   └── bell.mp3
│
├── logs
│
└── schedule-engine.py
```

```sh
Schedule
├── id
├── name
├── start_date
├── cycle_weeks
├── timezone (optional)
└── weeks

Week
└── weekdays

Day
└── event instances

Event Instance
├── title
├── start
├── end
├── color (optional)
├── metadata (optional)
└── notification profile

Notification Profile
├── before_minutes
└── methods
```
