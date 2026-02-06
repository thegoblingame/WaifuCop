# System Overview Specification

## Document Info
- **Version**: 1.0
- **Last Updated**: 2026-01-25
- **Status**: Active

---

## 1. Project Summary

**WaifuCop** is a productivity monitoring application that tracks computer usage via ActivityWatch, evaluates productivity using a local LLM, and delivers feedback through an anime-themed character ("waifu") interface. The system gamifies productivity through a daily "Waifu Meter" score that influences the character's mood and responses.

### Core Value Proposition
- Passive monitoring of computer activity
- AI-powered productivity assessment
- Gamified feedback loop with visual/emotional reinforcement
- Non-intrusive notifications that encourage focus

---

## 2. System Architecture

### 2.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL DEPENDENCIES                        │
├─────────────────────────────────────────────────────────────────────┤
│  ActivityWatch Server          Ollama LLM Server                    │
│  (localhost:5600)              (localhost:11434)                    │
│  - aw-watcher-window           - llama3.1:8b model                  │
│  - aw-watcher-afk                                                   │
└───────────────┬─────────────────────────┬───────────────────────────┘
                │                         │
                ▼                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         WAIFUCOP APPLICATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │  runner.py  │───▶│ aw_probe.py │───▶│     llama_query.py      │ │
│  │ (Scheduler) │    │  (Core)     │    │     (LLM Interface)     │ │
│  └─────────────┘    └──────┬──────┘    └─────────────────────────┘ │
│                            │                                        │
│                            ▼                                        │
│                    ┌───────────────┐                                │
│                    │  score.json   │                                │
│                    │ (Persistence) │                                │
│                    └───────┬───────┘                                │
│                            │                                        │
│              ┌─────────────┴─────────────┐                          │
│              ▼                           ▼                          │
│     ┌─────────────────┐        ┌──────────────────┐                │
│     │ waifu_popup.py  │        │discord_notifier.py│                │
│     │ (Desktop GUI)   │        │ (Webhook)        │                │
│     └─────────────────┘        └──────────────────┘                │
│                                                                     │
│     ┌─────────────────┐        ┌──────────────────┐                │
│     │ waifucops.yaml  │        │     .env         │                │
│     │ (Personas)      │        │ (Config)         │                │
│     └─────────────────┘        └──────────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| Scheduler | `runner.py` | Triggers checks at fixed intervals (default: 15 min) |
| Core Engine | `aw_probe.py` | Orchestrates data fetching, analysis, and output |
| Activity Tracker | `aw_probe.py` | Fetches and summarizes ActivityWatch events |
| LLM Interface | `llama_query.py` | Sends prompts to Ollama, parses responses |
| Desktop UI | `waifu_popup.py` | Renders popup window with character and message |
| Discord Output | `discord_notifier.py` | Sends messages via Discord webhook |
| Data Store | `score.json` | Persists daily scores and interval history |
| Persona Config | `waifucops.yaml` | Defines character attributes and images |

---

## 3. Data Flow

### 3.1 Single Interval Flow (Every 15 Minutes)

```
1. TRIGGER
   └── runner.py scheduler fires

2. DATA COLLECTION
   ├── Fetch AFK percentage from ActivityWatch
   │   └── If AFK > 50%: EXIT (no notification)
   └── Fetch window/app events for last 15 minutes

3. SUMMARIZATION
   └── Convert events to text format:
       "X.X min | app=AppName | title=WindowTitle"

4. CONTEXT LOADING
   ├── Read current waifu meter from score.json
   └── Read interval history (for streak detection)

5. LLM EVALUATION
   ├── Construct prompt with:
   │   ├── System prompt (persona, productive/unproductive lists)
   │   ├── Activity summary
   │   └── Escalation context (if applicable)
   └── Receive response: { score: 1-10, explanation: "..." }

6. SCORE UPDATE
   ├── Calculate meter delta based on LLM score + streaks
   ├── Update waifu meter (clamped 0-100)
   └── Write to score.json

7. OUTPUT
   ├── Determine mood from waifu meter (angry/neutral/happy)
   ├── Select appropriate character image
   └── Display via:
       ├── Desktop popup (primary)
       └── Discord webhook (alternative)
```

### 3.2 Daily Lifecycle

```
DAY START (First check of the day)
├── Detect new date
├── Reset waifu meter to 50
├── Clear interval history
└── Begin tracking

THROUGHOUT DAY
├── Every 15 minutes: Run interval flow
├── Accumulate interval history
└── Update waifu meter continuously

DAY END
└── Final state persisted in score.json
    (Available for historical analysis later)
```

---

## 4. External Dependencies

### 4.1 ActivityWatch
- **Purpose**: Tracks active windows and AFK status
- **Required Watchers**:
  - `aw-watcher-window`: Records active application and window title
  - `aw-watcher-afk`: Records keyboard/mouse activity
- **API Endpoint**: `http://localhost:5600`
- **Client Library**: `aw-client` (Python package)

### 4.2 Ollama
- **Purpose**: Local LLM inference for productivity evaluation
- **Model**: `llama3.1:8b`
- **API Endpoint**: `http://localhost:11434`
- **Required**: Must be running with model loaded before WaifuCop starts

### 4.3 Discord (Optional)
- **Purpose**: Alternative notification delivery
- **Requirement**: Valid webhook URL in `.env` file
- **When Used**: As replacement for desktop popup (user preference)

---

## 5. Configuration Files

| File | Format | Purpose |
|------|--------|---------|
| `waifucops.yaml` | YAML | Persona definitions (images, personality) |
| `score.json` | JSON | Runtime state and history |
| `.env` | Dotenv | Secrets (Discord webhook URL) |
| `pyproject.toml` | TOML | Python dependencies |

---

## 6. Runtime Requirements

### 6.1 System Requirements
- **OS**: Windows (primary), Linux/macOS (future)
- **Python**: 3.13.1+
- **Display**: Required for popup mode

### 6.2 Services That Must Be Running
1. ActivityWatch server with watchers active
2. Ollama server with llama3.1:8b model loaded

### 6.3 Installation (Current - Personal Use)
```bash
# Clone repository
git clone <repo-url>
cd WaifuCop

# Install dependencies
poetry install

# Configure .env (if using Discord)
echo "DISCORD_WEBHOOK_URL=your_webhook_url" > .env

# Run
poetry run python scripts/runner.py 15
```

---

## 7. Design Principles

### 7.1 Day Independence
Each day is treated as completely independent. The waifu meter resets to 50 at the start of each day. Performance does not carry over between days.

### 7.2 Non-Intrusive Monitoring
- AFK detection prevents notifications when user is away
- Popup has delayed close button (forces brief attention)
- Auto-close after 30 seconds (doesn't block workflow indefinitely)

### 7.3 Gamification
- Waifu meter provides continuous feedback
- Streaks reward consistency
- Character mood creates emotional connection to productivity

### 7.4 Local-First
- All processing happens locally
- No data sent to external servers (except optional Discord)
- Privacy-preserving by design

---

## 8. Future Considerations

### 8.1 Planned Enhancements
- Multiple personas with different personalities
- User-configurable productive/unproductive activity lists
- Packaging for distribution to other users
- Historical analytics and trends

### 8.2 Out of Scope (Current Version)
- Multi-user support
- Cloud synchronization
- Mobile notifications
- Cross-day performance tracking

---

## 9. Related Specifications

| Spec | Description |
|------|-------------|
| [waifu-meter.md](./waifu-meter.md) | Scoring algorithm details |
| [activity-tracking.md](./activity-tracking.md) | ActivityWatch integration |
| [llm-integration.md](./llm-integration.md) | LLM prompt and response handling |
| [popup-ui.md](./popup-ui.md) | Desktop popup interface |
| [personas.md](./personas.md) | Character system |
| [discord-integration.md](./discord-integration.md) | Discord webhook |
| [data-persistence.md](./data-persistence.md) | Data storage schema |
