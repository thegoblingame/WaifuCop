# Waifu Meter Specification

## Document Info

- **Version**: 1.0
- **Last Updated**: 2026-01-25
- **Status**: Active

---

## 1. Overview

The **Waifu Meter** is the core gamification mechanic of WaifuCop. It is a numerical score between 0 and 100 that represents the user's productivity standing for the current day. The meter influences:

- The character's mood (angry, neutral, happy)
- The tone of LLM-generated messages
- Visual feedback (character image selection)

---

## 2. Core Properties

| Property             | Value                                |
| -------------------- | ------------------------------------ |
| Minimum              | 0                                    |
| Maximum              | 100                                  |
| Daily Starting Value | 50                                   |
| Update Frequency     | Every interval (default: 15 minutes) |
| Reset Trigger        | New calendar day detected            |

---

## 3. Daily Lifecycle

### 3.1 Day Start

When the first check of a new day occurs:

1. Detect that `score.json` contains a different date than today
2. Archive previous day's final score (for future analytics)
3. Reset waifu meter to **50**
4. Clear interval history (streaks reset)

### 3.2 During Day

Each interval:

1. LLM evaluates activity and returns score (1-10)
2. Calculate meter delta based on LLM score and modifiers
3. Apply delta to current meter
4. Clamp result to [0, 100]
5. Persist to `score.json`

### 3.3 Day End

No special handling. The final meter value remains in `score.json` until the next day's first check triggers a reset.

---

## 4. Score Calculation

Not implemented yet

---

## 5. Mood Thresholds

The waifu meter determines the character's mood:

| Meter Range | Mood    | Image Used    |
| ----------- | ------- | ------------- |
| 0-30        | Angry   | `angry.png`   |
| 31-70       | Neutral | `neutral.png` |
| 71-100      | Happy   | `happy.png`   |

**Note**: Thresholds are inclusive on the lower bound. A meter of exactly 30 is "angry", exactly 31 is "neutral".

```python
def get_mood(waifu_meter: int) -> str:
    if waifu_meter <= 30:
        return "angry"
    elif waifu_meter <= 70:
        return "neutral"
    else:
        return "happy"
```

---

## 6. Streak Tracking

### 6.1 Data Structure

The interval history needed for streak calculation:

```python
{
    "intervals": [
        {"timestamp": "2026-01-25T09:00:00", "llm_score": 7, "direction": "productive"},
        {"timestamp": "2026-01-25T09:15:00", "llm_score": 8, "direction": "productive"},
        {"timestamp": "2026-01-25T09:30:00", "llm_score": 3, "direction": "unproductive"}
    ],
    "current_streak": {
        "direction": "unproductive",
        "count": 1
    }
}
```

### 6.2 Streak Update Logic

Not implemented yet

---

## 7. Edge Cases

### 7.1 First Interval of the Day

- No streak exists yet
- Multiplier is 1.0x
- Streak begins with this interval's direction

### 7.2 AFK Skip

When an interval is skipped due to AFK > 50%:

- Meter is **not** updated
- Streak is **preserved** (not broken)
- No entry added to interval history

### 7.3 Meter at Boundaries

- If meter is 0 and delta is negative: remains 0
- If meter is 100 and delta is positive: remains 100
- Streaks still accumulate even at boundaries

### 7.4 Rapid Recovery Prevention

The streak system naturally prevents rapid swings:

- Getting from 0 to 100 requires sustained productive behavior
- A single good interval after many bad ones has multiplier 1.0x

---

## 8. Future Enhancements

### 8.1 Persona-Specific Algorithms

Different personas may have different:

- Base delta mappings
- Streak multipliers
- Mood thresholds

This will be specified in `waifucops.yaml` per persona.

### 8.2 Configurable Parameters

Future versions may expose:

- Custom mood thresholds
- Adjustable base deltas
- Streak multiplier curves

### 8.3 Historical Trends

Using persisted daily scores:

- Weekly/monthly averages
- Trend visualization
- Achievement unlocks

---

## 9. Implementation Checklist

- [ ] `llm_score_to_base_delta()` function
- [ ] `get_streak_multiplier()` function
- [ ] `calculate_final_delta()` function
- [ ] `update_waifu_meter()` function
- [ ] `get_mood()` function
- [ ] Streak tracking in `score.json`
- [ ] Daily reset detection and handling
- [ ] AFK skip streak preservation

---

## 10. Related Specifications

| Spec                                         | Relevance                            |
| -------------------------------------------- | ------------------------------------ |
| [data-persistence.md](./data-persistence.md) | Storage schema for meter and streaks |
| [llm-integration.md](./llm-integration.md)   | How LLM scores are obtained          |
| [personas.md](./personas.md)                 | Future persona-specific algorithms   |
| [popup-ui.md](./popup-ui.md)                 | How mood affects display             |
