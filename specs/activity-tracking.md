# Activity Tracking Specification

## Document Info
- **Version**: 1.0
- **Last Updated**: 2026-01-25
- **Status**: Active

---

## 1. Overview

Activity tracking is the data collection layer of WaifuCop. It interfaces with ActivityWatch to gather information about what the user has been doing on their computer, then transforms that raw data into a format suitable for LLM evaluation.

---

## 2. ActivityWatch Integration

### 2.1 Required Components

| Component | Purpose |
|-----------|---------|
| ActivityWatch Server | Core service running on `localhost:5600` |
| aw-watcher-window | Tracks active application and window title |
| aw-watcher-afk | Tracks keyboard/mouse activity for AFK detection |

### 2.2 Bucket Discovery

ActivityWatch organizes data into "buckets". WaifuCop needs to discover two buckets:

**Window Bucket**:
- Pattern: `aw-watcher-window_<hostname>`
- Contains: Application name, window title, timestamps

**AFK Bucket**:
- Pattern: `aw-watcher-afk_<hostname>`
- Contains: AFK status ("afk" or "not-afk"), timestamps

```python
def find_window_bucket_id(aw_client) -> str:
    buckets = aw_client.get_buckets()
    for bucket_id in buckets:
        if bucket_id.startswith("aw-watcher-window"):
            return bucket_id
    raise Exception("Window watcher bucket not found")

def find_afk_bucket_id(aw_client) -> str:
    buckets = aw_client.get_buckets()
    for bucket_id in buckets:
        if bucket_id.startswith("aw-watcher-afk"):
            return bucket_id
    raise Exception("AFK watcher bucket not found")
```

---

## 3. AFK Detection

### 3.1 Purpose
Prevent notifications when the user is away from their computer. If the user was AFK for more than 50% of the interval, skip the check entirely.

### 3.2 Calculation

```python
def get_afk_fraction(aw_client, afk_bucket_id: str, minutes: int) -> float:
    """
    Calculate what fraction of the time window the user was AFK.

    Returns:
        Float between 0.0 and 1.0
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=minutes)

    events = aw_client.get_events(
        afk_bucket_id,
        start=start_time,
        end=end_time
    )

    total_seconds = minutes * 60
    afk_seconds = 0

    for event in events:
        if event.data.get("status") == "afk":
            afk_seconds += event.duration.total_seconds()

    return min(1.0, afk_seconds / total_seconds)
```

### 3.3 Threshold

| AFK Fraction | Action |
|--------------|--------|
| <= 0.50 | Proceed with evaluation |
| > 0.50 | Skip interval (no notification, preserve streak) |

---

## 4. Event Fetching

### 4.1 Time Window

Events are fetched for the configured interval (default: 15 minutes).

```python
def get_events_last_minutes(aw_client, window_bucket_id: str, afk_bucket_id: str, minutes: int):
    """
    Fetch window events for the last N minutes.

    Returns:
        List of events, or None if AFK > 50%
    """
    # First check AFK
    afk_fraction = get_afk_fraction(aw_client, afk_bucket_id, minutes)
    if afk_fraction > 0.5:
        return None  # Signal to skip this interval

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=minutes)

    events = aw_client.get_events(
        window_bucket_id,
        start=start_time,
        end=end_time
    )

    return events
```

### 4.2 Event Structure

Each event from ActivityWatch contains:

```python
{
    "timestamp": "2026-01-25T09:00:00.000Z",
    "duration": 45.5,  # seconds
    "data": {
        "app": "Code.exe",
        "title": "main.py - WaifuCop - Visual Studio Code"
    }
}
```

---

## 5. Event Summarization

### 5.1 Purpose
Convert raw events into human-readable text that the LLM can evaluate.

### 5.2 Aggregation Logic

Events are grouped by (app, title) tuple and aggregated by duration:

```python
def summarize_events(events) -> str:
    """
    Convert events to a text summary.

    Returns:
        Formatted string with one line per activity
    """
    # Group by (app, title)
    activity_durations = {}

    for event in events:
        app = event.data.get("app", "Unknown")
        title = event.data.get("title", "Unknown")
        key = (app, title)

        duration_minutes = event.duration.total_seconds() / 60

        if key in activity_durations:
            activity_durations[key] += duration_minutes
        else:
            activity_durations[key] = duration_minutes

    # Filter out very short activities (< 0.3 minutes / 18 seconds)
    MIN_DURATION = 0.3
    filtered = {k: v for k, v in activity_durations.items() if v >= MIN_DURATION}

    # Sort by duration (descending)
    sorted_activities = sorted(filtered.items(), key=lambda x: x[1], reverse=True)

    # Format output
    lines = []
    for (app, title), minutes in sorted_activities:
        lines.append(f"{minutes:.1f} min | app={app} | title={title}")

    return "\n".join(lines)
```

### 5.3 Output Format

```
7.2 min | app=Code.exe | title=waifu_meter.py - WaifuCop - Visual Studio Code
4.5 min | app=firefox.exe | title=Stack Overflow - Python datetime
2.1 min | app=Discord.exe | title=Discord
1.2 min | app=explorer.exe | title=WaifuCop
```

### 5.4 Filtering Rules

| Rule | Threshold | Reason |
|------|-----------|--------|
| Minimum duration | 0.3 minutes (18 sec) | Filter out transient window switches |

---

## 6. Interval Configuration

### 6.1 Default Interval
- **Value**: 15 minutes
- **Configurable**: Yes, via command-line argument to `runner.py`

### 6.2 Recommended Intervals

| Interval | Use Case |
|----------|----------|
| 15 min | Standard monitoring (recommended) |
| 30 min | Less intrusive monitoring |
| 60 min | Minimal interruption |
| 5 min | Testing/debugging only |

### 6.3 Interval Constraints
- Minimum: 1 minute (practical limit)
- Maximum: No hard limit, but effectiveness decreases beyond 60 minutes

---

## 7. Error Handling

### 7.1 ActivityWatch Not Running

```python
def safe_fetch_events(minutes: int):
    try:
        client = ActivityWatchClient("waifucop")
        # ... fetch logic
    except ConnectionError:
        print("ActivityWatch server not running. Skipping interval.")
        return None
```

### 7.2 Missing Buckets

If window or AFK bucket is not found:
- Log warning
- Skip interval
- Do not crash the scheduler

### 7.3 Empty Events

If no events are returned (user did nothing trackable):
- Skip interval
- Preserve streak
- No notification

---

## 8. Privacy Considerations

### 8.1 Data Handling
- All data stays local (ActivityWatch stores on disk)
- Event data is only used in-memory for summarization
- Full window titles are sent to local LLM (not external)

### 8.2 Sensitive Window Filtering (Future)
Consider filtering out sensitive windows:
- Password managers
- Banking applications
- Private browsing windows

---

## 9. Implementation Checklist

- [x] `find_window_bucket_id()` function
- [x] `find_afk_bucket_id()` function
- [x] `get_afk_fraction()` function
- [x] `get_events_last_minutes()` function with AFK check
- [x] `summarize_events()` function
- [x] Error handling for ActivityWatch connection
- [x] Error handling for missing buckets
- [x] Configurable interval parameter

---

## 10. Related Specifications

| Spec | Relevance |
|------|-----------|
| [system-overview.md](./system-overview.md) | Where activity tracking fits in the system |
| [llm-integration.md](./llm-integration.md) | How summaries are sent to LLM |
| [waifu-meter.md](./waifu-meter.md) | AFK skip behavior and streak preservation |
