WaifuCop Project Overview

WaifuCop is a productivity monitoring application that uses https://activitywatch.net/ to track your computer usage and provides feedback through an anime-themed "waifu" character. It evaluates how productively
you've been using your time and delivers assessments via desktop popups (and optionally Discord notifications).

---

File Breakdown

1. scripts/runner.py

Purpose: Main scheduler/entry point for the application.

- Uses the schedule library to run the productivity check at regular intervals (default: every 60 minutes, configurable via command-line argument)
- Calls aw_probe.main() on each interval to fetch activity data and deliver feedback
- Runs in an infinite loop, checking pending scheduled jobs every second

---

2. scripts/aw_probe.py

Purpose: Core logic for fetching and analyzing ActivityWatch data.

- Connects to the local ActivityWatch server using aw_client
- Finds the aw-watcher-window bucket to get window/app activity events
- Finds the aw-watcher-afk bucket to determine if the user was AFK (away from keyboard)
- If the user was AFK for more than 50% of the interval, it skips the "nag" to avoid bothering someone who wasn't at their computer
- Summarizes window events by app and title with time spent
- Sends the summary to a local LLM (Llama) for productivity evaluation
- Displays the result via a popup window (using waifu_popup.py)
- Has commented-out code for Discord webhook notifications as an alternative delivery method

---

3. scripts/llama_query.py

Purpose: Interface to a local Ollama LLM server.

- Connects to localhost:11434 (Ollama's default port) using the llama3.1:8b model
- Contains a detailed system prompt that defines "waifucop" as a tsundere anime supervisor character
- The prompt includes rules for what's considered productive (VS Code, programming) vs. unproductive (Twitter/X, YouTube, Messenger)
- Asks the LLM to rate productivity 1-10 with a brief explanation
- Returns the LLM's response as a string

---

4. scripts/waifu_popup.py

Purpose: Displays a GUI popup window with the waifu image and message.

- Uses tkinter for the GUI and PIL (Pillow) for image handling
- Creates a borderless, always-on-top popup window
- Features:
  - Dark themed UI with a Windows-style header bar
  - Draggable window
  - Close button (disabled for 3 seconds to force reading)
  - Typewriter effect for the message text
  - Auto-closes after 30 seconds (or after message finishes typing)
- Shows the waifu image on the left and the productivity message on the right

---

5. scripts/discord_notifier.py

Purpose: Sends messages to Discord via webhook (optional alternative to popup).

- Loads the webhook URL from a .env file (DISCORD_WEBHOOK_URL)
- Posts messages to the webhook with a custom username ("waifucop") and avatar
- Currently commented out in the main flow but available as an alternative notification method

---

Supporting Files

- waifu_images/: Contains the waifu character images (happy_waifu.png, angry_waifu.png, neutral_waifu.png) displayed in popups
- pyproject.toml: Poetry dependency management, requiring Python 3.13.1+, aw-client, schedule, requests, python-dotenv, pillow, and pyyaml
- waifus.yaml: Configuration file (currently empty)

---

How It Works (Flow)

1. User runs runner.py (optionally with minutes argument)
2. Every N minutes, aw_probe.main() is called
3. It fetches the last N minutes of window activity from ActivityWatch
4. If user was mostly AFK (>50%), it skips
5. Activity is summarized and sent to local Llama LLM
6. LLM responds with a productivity score and tsundere-style explanation
7. A popup appears with a waifu image and the message
