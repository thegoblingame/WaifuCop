# Data Persistence Specification

## Document Info
- **Version**: 1.1
- **Last Updated**: 2026-01-26
- **Status**: Active

---

## 1. Overview

Data persistence handles the storage and retrieval of WaifuCop's runtime state. The system uses a **two-file architecture** to separate concerns between frequently-updated daily state and append-only historical records.

---

## 2. Storage Files

### 2.1 Two-File Architecture

| File | Format | Purpose | Write Frequency |
|------|--------|---------|-----------------|
| `daily_score.json` | JSON | Current day's meter, intervals, streak | Every 15 minutes |
| `score_history.json` | JSON | Archive of past days' final scores | Once per day |

### 2.2 Rationale

**Why two files instead of one?**

1. **Different access patterns**: Daily file is read/written every 15 minutes; history is appended once per day
2. **Cleaner daily reset**: Overwrite daily file instead of surgically updating a combined file
3. **Corruption isolation**: If daily file corrupts, historical data remains safe
4. **Simpler queries**: Reading today's meter doesn't require filtering through historical entries
5. **Performance**: Frequent operations stay fast on a small file

### 2.3 Configuration Files (Read-Only)

| File | Format | Purpose |
|------|--------|---------|
| `waifucops.yaml` | YAML | Persona definitions |
| `.env` | Dotenv | Secrets (Discord webhook) |

---

## 3. daily_score.json Schema

### 3.1 Schema Definition

```json
{
  "date": "2026-01-25",
  "current_waifu_meter": 67,
  "history": [
    {
      "timestamp": "2026-01-25T09:00:00",
      "llm_score": 7
    },
    {
      "timestamp": "2026-01-25T09:15:00",
      "llm_score": 8
    }
  ]
}
```

### 3.2 Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `date` | string (ISO date) | Current tracking date (YYYY-MM-DD) |
| `current_waifu_meter` | integer (0-100) | Current meter value |
| `history` | array | History of today's intervals |

### 3.3 History Entry Object

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (ISO datetime) | When the interval was evaluated |
| `llm_score` | integer (1-10) | Score returned by LLM |

### 3.4 Default State

When no daily file exists or it's a new day:

```python
DEFAULT_DAILY_STATE = {
    "date": None,
    "current_waifu_meter": 50,
    "history": []
}
```

---

## 4. score_history.json Schema

### 4.1 Schema Definition

The history file is simply an array of daily score objects. At the end of each day, the object from `daily_score.json` is moved directly into this array.

```json
[
  {
    "date": "2026-01-23",
    "current_waifu_meter": 72,
    "history": [
      {"timestamp": "2026-01-23T09:00:00", "llm_score": 7},
      {"timestamp": "2026-01-23T09:15:00", "llm_score": 8},
      {"timestamp": "2026-01-23T09:30:00", "llm_score": 6}
    ]
  },
  {
    "date": "2026-01-24",
    "current_waifu_meter": 45,
    "history": [
      {"timestamp": "2026-01-24T09:00:00", "llm_score": 3},
      {"timestamp": "2026-01-24T09:15:00", "llm_score": 4}
    ]
  }
]
```

### 4.2 Default History

When no history file exists:

```python
DEFAULT_HISTORY = []
```

---

## 5. Daily Operations

### 5.1 Load Daily State

```python
import json
from datetime import date

DAILY_FILE = "daily_score.json"

DEFAULT_DAILY_STATE = {
    "date": None,
    "current_waifu_meter": 50,
    "history": []
}

def load_daily_state() -> dict:
    """Load current day's state from file."""
    try:
        with open(DAILY_FILE, "r") as f:
            state = json.load(f)
        return state
    except FileNotFoundError:
        return DEFAULT_DAILY_STATE.copy()
    except json.JSONDecodeError:
        print("Warning: Corrupted daily_score.json, using defaults")
        return DEFAULT_DAILY_STATE.copy()
```

### 5.2 Save Daily State

```python
def save_daily_state(state: dict):
    """Save current day's state to file."""
    with open(DAILY_FILE, "w") as f:
        json.dump(state, f, indent=2)
```

### 5.3 Check for New Day

```python
def is_new_day(state: dict) -> bool:
    """Check if we need to reset for a new day."""
    today = date.today().isoformat()
    return state.get("date") != today
```

### 5.4 Record Interval

```python
from datetime import datetime

def record_interval(
    state: dict,
    llm_score: int,
    new_meter: int
) -> dict:
    """Record a completed interval in daily state."""

    # Create history entry
    entry = {
        "timestamp": datetime.now().isoformat(),
        "llm_score": llm_score
    }

    state["history"].append(entry)
    state["current_waifu_meter"] = new_meter

    return state
```

### 5.5 Get Current Meter

```python
def get_waifu_meter(state: dict) -> int:
    """Get current waifu meter value."""
    return state.get("current_waifu_meter", 50)
```

### 5.6 Get History

```python
def get_history(state: dict) -> list:
    """Get today's interval history."""
    return state.get("history", [])
```

---

## 6. History Operations

### 6.1 Load History

```python
HISTORY_FILE = "score_history.json"

DEFAULT_HISTORY = []

def load_history() -> list:
    """Load historical scores from file."""
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        return history
    except FileNotFoundError:
        return DEFAULT_HISTORY.copy()
    except json.JSONDecodeError:
        print("Warning: Corrupted score_history.json, using defaults")
        return DEFAULT_HISTORY.copy()
```

### 6.2 Save History

```python
def save_history(history: list):
    """Save historical scores to file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
```

### 6.3 Archive Day

```python
def archive_day(daily_state: dict, history: list) -> list:
    """
    Archive a completed day's data to history.
    Called during day transition.

    Simply appends the daily_state object to the history array.
    """
    history.append(daily_state)
    return history
```

---

## 7. Day Transition

### 7.1 Transition Workflow

When a new day is detected:

```
1. Load current daily_state
2. Load history
3. Archive daily_state to history (if daily_state has data)
4. Save history
5. Reset daily_state for new day
6. Save daily_state
```

### 7.2 Implementation

```python
def handle_day_transition() -> dict:
    """
    Handle the transition from one day to the next.
    Returns the fresh daily state for the new day.
    """
    daily_state = load_daily_state()

    # Only archive if there's actual data from the previous day
    if daily_state.get("date") and daily_state.get("history"):
        history = load_history()
        history = archive_day(daily_state, history)
        save_history(history)  # Save history FIRST

    # Reset for new day
    new_state = {
        "date": date.today().isoformat(),
        "current_waifu_meter": 50,
        "history": []
    }
    save_daily_state(new_state)

    return new_state
```

### 7.3 Atomicity Considerations

The order of operations matters:
1. **Save history first**: If we crash after saving history but before resetting daily, we might archive the same day twice on next run. This is detectable (duplicate dates) and recoverable.
2. **Then reset daily**: If we crash here, we just start fresh, which is fine.

The reverse order (reset daily first, then save history) risks **data loss** - if we crash after reset but before archiving, we lose the day's data permanently.

---

## 8. Main Loop Integration

### 8.1 Interval Handler

```python
def handle_interval(llm_score: int, new_meter: int):
    """
    Called every 15 minutes after LLM evaluation.
    Handles day transitions and records the interval.
    """
    daily_state = load_daily_state()

    # Check for day transition
    if is_new_day(daily_state):
        daily_state = handle_day_transition()

    # Ensure date is set (first interval of the day)
    if daily_state.get("date") is None:
        daily_state["date"] = date.today().isoformat()

    # Record this interval
    daily_state = record_interval(daily_state, llm_score, new_meter)

    # Persist
    save_daily_state(daily_state)

    return daily_state
```

---

## 9. File Locations

### 9.1 Current Location (Personal Use)

```
C:\Users\khaaa\Desktop\WaifuCop\daily_score.json
C:\Users\khaaa\Desktop\WaifuCop\score_history.json
```

### 9.2 Future: Portable Location

```python
import os

def get_data_dir() -> str:
    """Get platform-appropriate data directory."""
    if os.name == 'nt':  # Windows
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(base, 'WaifuCop')
    else:  # Linux/macOS
        base = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
        return os.path.join(base, 'waifucop')

def get_daily_file() -> str:
    return os.path.join(get_data_dir(), 'daily_score.json')

def get_history_file() -> str:
    return os.path.join(get_data_dir(), 'score_history.json')
```

---

## 10. Error Handling

### 10.1 Corrupted Daily File

- Log warning
- Reset to default daily state
- User loses today's progress but app continues
- History remains intact

### 10.2 Corrupted History File

- Log warning
- Reset to empty history
- Daily tracking continues unaffected
- Historical data is lost (consider backups)

### 10.3 Disk Full / Write Failure

- Log error
- Continue operation in memory
- Retry on next interval
- Don't crash the scheduler

---

## 11. Implementation Checklist

### 11.1 Daily File Operations
- [ ] `load_daily_state()` function
- [ ] `save_daily_state()` function
- [ ] `is_new_day()` check
- [ ] `record_interval()` function
- [ ] `get_waifu_meter()` function
- [ ] `get_history()` function

### 11.2 History File Operations
- [ ] `load_history()` function
- [ ] `save_history()` function
- [ ] `archive_day()` function

### 11.3 Day Transition
- [ ] `handle_day_transition()` function
- [ ] `handle_interval()` main integration function

---

## 12. Related Specifications

| Spec | Relevance |
|------|-----------|
| [waifu-meter.md](./waifu-meter.md) | Defines scoring logic that generates data |
| [system-overview.md](./system-overview.md) | Where persistence fits in the system |
| [llm-integration.md](./llm-integration.md) | Source of llm_score values |
| [activity-tracking.md](./activity-tracking.md) | Source of interval triggers |
