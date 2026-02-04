# Discord Integration Specification

## Document Info
- **Version**: 1.0
- **Last Updated**: 2026-01-25
- **Status**: Active

---

## 1. Overview

Discord integration provides an alternative notification delivery method for WaifuCop. Instead of (or in addition to) the desktop popup, users can receive productivity feedback via Discord webhook messages.

---

## 2. Use Cases

### 2.1 Primary Use Case
Users who don't want to install the full desktop application can use Discord-only mode:
- Simpler setup (no Python environment needed on target machine)
- Works across devices (phone notifications)
- Less intrusive than popup windows

### 2.2 Secondary Use Case
Parallel notifications for logging/archival:
- Desktop popup for immediate feedback
- Discord for persistent record

---

## 3. Configuration

### 3.1 Environment Variable

Discord webhook URL is stored in `.env`:

```bash
# .env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/abcdefghijklmnop
```

### 3.2 Loading Configuration

```python
import os
from dotenv import load_dotenv

def get_discord_webhook_url() -> str | None:
    """Load Discord webhook URL from environment."""
    load_dotenv()
    return os.getenv("DISCORD_WEBHOOK_URL")

def is_discord_enabled() -> bool:
    """Check if Discord integration is configured."""
    url = get_discord_webhook_url()
    return url is not None and len(url) > 0
```

---

## 4. Message Format

### 4.1 Basic Message Structure

```python
{
    "username": "WaifuCop",
    "avatar_url": "https://i.imgur.com/zxLfvT3.jpeg",
    "content": "<message text>"
}
```

### 4.2 Message Content

The message sent to Discord contains:
1. The LLM-generated explanation
2. Current waifu meter score
3. Mood indicator

**Format**:
```
**Productivity Check** 📊

{llm_explanation}

**Waifu Meter:** {score}/100 {mood_emoji}
```

**Example**:
```
**Productivity Check** 📊

You've been mostly focused on coding in VS Code, which is great!
I noticed a quick Discord check - try to minimize distractions.
Keep up the good work!

**Waifu Meter:** 67/100 😐
```

### 4.3 Mood Emojis

| Mood | Emoji |
|------|-------|
| Angry (0-30) | 😠 |
| Neutral (31-70) | 😐 |
| Happy (71-100) | 😊 |

---

## 5. Implementation

### 5.1 Send Function

```python
import requests

def send_discord_message(
    message: str,
    waifu_meter: int,
    webhook_url: str = None
) -> bool:
    """
    Send a productivity message to Discord.

    Args:
        message: LLM-generated explanation
        waifu_meter: Current meter score (0-100)
        webhook_url: Discord webhook URL (uses env if not provided)

    Returns:
        True if successful, False otherwise
    """
    if webhook_url is None:
        webhook_url = get_discord_webhook_url()

    if not webhook_url:
        print("Discord webhook URL not configured")
        return False

    # Determine mood emoji
    if waifu_meter <= 30:
        mood_emoji = "😠"
    elif waifu_meter <= 70:
        mood_emoji = "😐"
    else:
        mood_emoji = "😊"

    # Format full message
    full_message = f"""**Productivity Check** 📊

{message}

**Waifu Meter:** {waifu_meter}/100 {mood_emoji}"""

    payload = {
        "username": "WaifuCop",
        "avatar_url": "https://i.imgur.com/zxLfvT3.jpeg",
        "content": full_message
    }

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        print(f"Discord webhook failed: {e}")
        return False
```

### 5.2 Rich Embed Format (Future Enhancement)

For more visually appealing messages:

```python
def send_discord_embed(
    message: str,
    waifu_meter: int,
    webhook_url: str = None
) -> bool:
    """Send a rich embed message to Discord."""

    # Determine color based on mood
    if waifu_meter <= 30:
        color = 0xFF0000  # Red
        mood = "Angry"
    elif waifu_meter <= 70:
        color = 0xFFFF00  # Yellow
        mood = "Neutral"
    else:
        color = 0x00FF00  # Green
        mood = "Happy"

    payload = {
        "username": "WaifuCop",
        "avatar_url": "https://i.imgur.com/zxLfvT3.jpeg",
        "embeds": [{
            "title": "Productivity Check",
            "description": message,
            "color": color,
            "fields": [
                {
                    "name": "Waifu Meter",
                    "value": f"{waifu_meter}/100",
                    "inline": True
                },
                {
                    "name": "Mood",
                    "value": mood,
                    "inline": True
                }
            ],
            "footer": {
                "text": "WaifuCop Productivity Monitor"
            }
        }]
    }

    # ... send request
```

---

## 6. Delivery Modes

### 6.1 Mode Configuration

```python
# Future: configurable in settings
DELIVERY_MODE = "popup"  # Options: "popup", "discord", "both"

def deliver_notification(
    message: str,
    waifu_meter: int,
    persona: dict,
    mode: str = DELIVERY_MODE
):
    """Deliver notification via configured channel(s)."""

    if mode in ("popup", "both"):
        img_path = get_persona_image(persona, get_mood(waifu_meter))
        show_popup(img_path, message, waifu_meter)

    if mode in ("discord", "both"):
        send_discord_message(message, waifu_meter)
```

### 6.2 Mode Comparison

| Mode | Desktop Required | Persistent Record | Visual Character |
|------|------------------|-------------------|------------------|
| popup | Yes | No | Yes |
| discord | No | Yes | No (avatar only) |
| both | Yes | Yes | Yes |

---

## 7. Error Handling

### 7.1 Webhook Errors

| Error | Handling |
|-------|----------|
| Invalid URL | Log error, skip Discord delivery |
| Network timeout | Log error, continue (don't block popup) |
| Rate limited (429) | Log warning, skip this notification |
| Server error (5xx) | Log error, continue |

### 7.2 Graceful Degradation

Discord errors should never crash the application:

```python
def safe_send_discord(message: str, waifu_meter: int):
    """Safely attempt Discord delivery."""
    try:
        send_discord_message(message, waifu_meter)
    except Exception as e:
        print(f"Discord delivery failed (non-critical): {e}")
        # Continue execution - popup still works
```

---

## 8. Rate Limiting

### 8.1 Discord Limits

Discord webhooks have rate limits:
- ~30 messages per minute per webhook
- 2000 characters per message

### 8.2 WaifuCop Default Behavior

With 15-minute intervals, rate limiting is not a concern:
- 4 messages per hour
- Well under Discord limits

### 8.3 Handling Rate Limits

If rate limited (HTTP 429):
- Log the event
- Skip this notification
- Do not retry (next interval will work)

---

## 9. Security Considerations

### 9.1 Webhook URL Protection

- Store in `.env` (not committed to git)
- `.env` is in `.gitignore`
- Never log the full webhook URL

### 9.2 Message Content

- Activity data is sent to Discord servers
- Users should be aware their activity summary goes through Discord
- Consider privacy implications before enabling

---

## 10. Setup Instructions

### 10.1 Creating a Discord Webhook

1. Open Discord and go to your server
2. Right-click the channel for notifications
3. Select "Edit Channel" → "Integrations"
4. Click "Create Webhook"
5. Name it "WaifuCop" (optional)
6. Copy the webhook URL

### 10.2 Configuring WaifuCop

1. Create `.env` file in project root (if not exists)
2. Add the webhook URL:
   ```
   DISCORD_WEBHOOK_URL=<your webhook URL>
   ```
3. Restart WaifuCop

---

## 11. Implementation Checklist

- [x] Basic `send_discord_message()` function
- [ ] Proper message formatting with meter display
- [ ] Mood emoji integration
- [ ] Error handling and logging
- [ ] Environment variable loading
- [ ] `is_discord_enabled()` check
- [ ] Integration with main notification flow
- [ ] Rich embed format (future)
- [ ] Delivery mode configuration (future)

---

## 12. Related Specifications

| Spec | Relevance |
|------|-----------|
| [system-overview.md](./system-overview.md) | Discord as alternative output |
| [llm-integration.md](./llm-integration.md) | Source of message content |
| [waifu-meter.md](./waifu-meter.md) | Meter score for display |
| [popup-ui.md](./popup-ui.md) | Alternative/parallel delivery |
