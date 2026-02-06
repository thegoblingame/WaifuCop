# Popup UI Specification

## Document Info
- **Version**: 1.0
- **Last Updated**: 2026-01-25
- **Status**: Active

---

## 1. Overview

The popup UI is the primary visual feedback mechanism for WaifuCop. It displays the waifu character alongside the LLM-generated productivity message, creating an engaging and memorable notification experience.

---

## 2. Window Properties

### 2.1 Basic Properties

| Property | Value |
|----------|-------|
| Framework | PySide6 (Qt 6) |
| Window Type | `QWidget` (frameless via `Qt.FramelessWindowHint`) |
| Default Size | 40% screen width x 45% screen height (percentage-based) |
| Position | Centered horizontally, placed at 1/3 from top vertically |
| Always on Top | Yes (`Qt.WindowStaysOnTopHint`) |
| Resizable | No (frameless, fixed size) |

### 2.2 Window Behavior

Window dimensions are percentage-based for cross-platform consistency across different screen resolutions.

```python
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

app = QApplication.instance() or QApplication(sys.argv)

window = QWidget()
window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

# Percentage-based sizing
screen = app.primaryScreen().geometry()
screen_w, screen_h = screen.width(), screen.height()
width = int(screen_w * width_pct)   # default 0.40
height = int(screen_h * height_pct) # default 0.45

# Centered horizontally, 1/3 from top vertically
window.setFixedSize(width, height)
window.move((screen_w - width) // 2, (screen_h - height) // 3)
```

---

## 3. Visual Design

### 3.1 Color Scheme

| Element | Color | Hex Code |
|---------|-------|----------|
| Background | Dark Gray | `#333333` |
| Header Bar | Windows Blue | `#0078d4` |
| Header Text | White | `#FFFFFF` |
| Body Text | White | `#FFFFFF` |
| Close Button (Normal) | Header color | `#0078d4` |
| Close Button (Hover) | Windows-style Red | `#c42b1c` |
| Close Button (Disabled) | Gray | `#888888` |
| Waifu Meter Score | Gray | `#888888` |

### 3.2 Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ [Header Bar - #0078d4]                              [X] Close   │
│  "WaifuCop"                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌────────────────────────────────────┐│
│  │                  │    │                                    ││
│  │                  │    │  Message text appears here with    ││
│  │   Waifu Image    │    │  typewriter effect...              ││
│  │                  │    │                                    ││
│  │                  │    │                                    ││
│  │                  │    │                                    ││
│  └──────────────────┘    │                                    ││
│                          │                    ┌──────────────┐││
│                          │                    │ Waifu Meter  │││
│                          │                    │     67       │││
│                          │                    └──────────────┘││
│                          └────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Component Dimensions

Dimensions scale with the percentage-based window size. These are approximate for a 1920x1080 screen:

| Component | Width | Height | Position |
|-----------|-------|--------|----------|
| Header Bar | Full width | 30px | Top, via `QHBoxLayout` |
| Waifu Image Area | Scales to fit | Window height - 70px | Left side |
| Message Area | Window width - image width - 60px | Fills remaining | Right side |
| Waifu Meter Display | Auto | Auto | Absolute bottom-right (via layout alignment) |

---

## 4. Image Display

### 4.1 Image Selection

The displayed image depends on the current waifu meter score:

| Meter Range | Mood | Image File |
|-------------|------|------------|
| 0-30 | Angry | `waifu_images/<persona>/angry.png` |
| 31-70 | Neutral | `waifu_images/<persona>/neutral.png` |
| 71-100 | Happy | `waifu_images/<persona>/happy.png` |

```python
def get_image_path(persona_id: str, waifu_meter: int) -> str:
    if waifu_meter <= 30:
        mood = "angry"
    elif waifu_meter <= 70:
        mood = "neutral"
    else:
        mood = "happy"

    return f"waifu_images/{persona_id}/{mood}.png"
```

### 4.2 Image Scaling

Images are scaled based on target height (window height minus header/padding) while maintaining aspect ratio. Width is not independently constrained — it scales proportionally with height.

```python
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

target_h = height - 70  # leave room for header + padding
pixmap = QPixmap(img_path)
pixmap = pixmap.scaledToHeight(target_h, Qt.SmoothTransformation)
```

The resulting image width is then used to calculate the text area's word-wrap width dynamically:
```python
wrap_width = width - pixmap.width() - 60
```

---

## 5. Text Display

### 5.1 Typewriter Effect

The message is displayed character-by-character to create engagement. A `QTimer` drives the animation and is tracked so it can be stopped on early window close.

```python
from PySide6.QtCore import QTimer

typing_delay_ms = 20
typing_index = 0

typing_timer = QTimer()
typing_timer.setInterval(typing_delay_ms)

def type_writer():
    nonlocal typing_index
    if typing_index <= len(message):
        text_label.setText(message[:typing_index])
        typing_index += 1
    else:
        typing_timer.stop()

typing_timer.timeout.connect(type_writer)
typing_timer.start()
```

### 5.2 Text Styling

| Property | Value |
|----------|-------|
| Font Family | Allerta |
| Font Size | 16pt (body), 16pt bold (header/close button), 12pt (score) |
| Color | White (`#FFFFFF`) |
| Wrapping | Word wrap, dynamic `wraplength` based on remaining width |
| Alignment | Left-aligned (`justify="left"`, `anchor="nw"`) |

---

## 6. Close Button Behavior

### 6.1 Implementation

The close button is implemented as a `QLabel` with mouse event handling. It uses the "✕" character and event filter or subclass for hover/click behavior.

A boolean flag gates all interactions — hover, leave, and click handlers check this flag before acting.

### 6.2 Delayed Enable

The close button is disabled for the first 3 seconds to ensure the user sees the message. On enable, the text color changes from gray to white and the cursor changes to a hand pointer.

```python
from PySide6.QtCore import QTimer, Qt

# Initially disabled
close_btn = QLabel("✕")
close_btn.setStyleSheet("color: #888888;")
close_btn.setCursor(Qt.ArrowCursor)
close_btn_enabled = False

def enable_close_btn():
    nonlocal close_btn_enabled
    close_btn_enabled = True
    close_btn.setStyleSheet("color: white;")
    close_btn.setCursor(Qt.PointingHandCursor)

QTimer.singleShot(3000, enable_close_btn)
```

### 6.3 Hover Effect

When enabled, the close button shows visual feedback on hover:
- Normal: Header color (`#0078d4`)
- Hover: Windows-style red (`#c42b1c`)

### 6.4 Cursor Feedback

| State | Cursor |
|-------|--------|
| Disabled (first 3s) | `Qt.ArrowCursor` (default) |
| Enabled | `Qt.PointingHandCursor` (pointer) |

---

## 7. Window Lifecycle

### 7.1 Auto-Close Logic

The window auto-closes after the **greater** of:
1. The `duration_ms` parameter (default 30 seconds)
2. The total typewriter typing time + 1 second buffer

This is calculated upfront as a single `QTimer.singleShot` call, not a polling loop:

```python
if duration_ms > 0:
    total_typing_time = typing_delay_ms * len(message)
    close_after = max(duration_ms, total_typing_time + 1000)
    QTimer.singleShot(close_after, close)
```

Auto-close is only set up if `duration_ms > 0`, allowing callers to disable it by passing `0`.

### 7.2 Manual Close

User can close the window after the 3-second delay by clicking the close button.
- (Future: Pressing Escape key)

### 7.3 Cleanup on Close

The `close()` function stops any running timers before closing the window to prevent errors from orphaned callbacks:

```python
def close():
    typing_timer.stop()
    window.close()
```

### 7.4 Window Existence Guards

Both the typewriter effect and the close button enable timer check `window.isVisible()` before acting, preventing errors if the window has already been closed.

---

## 8. Waifu Meter Display

### 8.1 Visual Representation

The waifu meter score is displayed as a plain number in the bottom-right corner using layout alignment. No label or border — just the number in gray (`#888888`).

### 8.2 Optional Display

The waifu meter display is conditional. If `waifu_meter` is `None`, the score is not shown at all. This allows callers to hide the meter when a score is not available.

### 8.3 Color Coding (Future Enhancement)

| Meter Range | Color |
|-------------|-------|
| 0-30 | Red |
| 31-70 | Yellow |
| 71-100 | Green |

---

## 9. Parameters

### 9.1 Function Signature

```python
def show_waifu_popup(
    img_path: str,
    message: str,
    waifu_meter: int | None = 50,
    title: str = "waifucop",
    width_pct: float = 0.40,
    height_pct: float = 0.45,
    duration_ms: int = 30000,
) -> None:
    """
    Display the waifu popup window.

    Args:
        img_path: Path to the waifu image file
        message: LLM-generated message to display
        waifu_meter: Current meter score (0-100), or None to hide the score
        title: Header bar title text
        width_pct: Window width as a fraction of screen width (0.0–1.0)
        height_pct: Window height as a fraction of screen height (0.0–1.0)
        duration_ms: Minimum display time before auto-close (0 to disable)
    """
```

### 9.2 Command-Line Interface

For testing and external invocation:

```bash
python scripts/waifu_popup.py <image_path> <message> <waifu_meter>
```

Note: The script lives in `scripts/` and resolves `PROJECT_ROOT` as its parent directory.

### 9.3 Debug Logging

On startup, the script appends `sys.argv` to `PROJECT_ROOT/debug.txt` for troubleshooting invocation issues.

---

## 10. Error Handling

### 10.1 Missing Image

If the specified image file doesn't exist:
- Log warning
- Use a fallback/default image
- Do not crash

```python
from PySide6.QtGui import QPixmap

def safe_load_image(path: str, fallback_path: str) -> QPixmap:
    pixmap = QPixmap(path)
    if pixmap.isNull():
        print(f"Warning: Image not found or failed to load: {path}")
        pixmap = QPixmap(fallback_path)
    return pixmap
```

### 10.2 Display Errors

If PySide6 fails to create the window:
- Log error with details
- Fail gracefully (scheduler continues)

---

## 11. Accessibility Considerations

### 11.1 Current Implementation
- High contrast (white on dark)
- Reasonably sized text
- Forced reading time (3-second delay)

### 11.2 Future Enhancements
- Configurable font size
- Configurable display duration
- Keyboard navigation (Escape to close)
- Screen reader compatibility

---

## 12. Implementation Checklist

- [x] Window creation with borderless/topmost settings
- [x] Percentage-based window sizing
- [x] Header bar with title and close button (Label-based, cross-platform)
- [x] Image loading and height-based scaling
- [ ] Image selection based on waifu meter (mood-based path resolution)
- [x] Typewriter effect for message
- [x] 3-second close button delay with cursor feedback
- [x] Hover effect on close button
- [x] Auto-close after max(duration, typing time + 1s)
- [x] Callback cancellation on close
- [x] `isVisible()` guards
- [x] Optional waifu meter display
- [x] Command-line interface for testing
- [x] Debug logging (`debug.txt`)
- [ ] Error handling for missing images (fallback image)
- [ ] Keyboard close (Escape key)

---

## 13. Related Specifications

| Spec | Relevance |
|------|-----------|
| [waifu-meter.md](./waifu-meter.md) | Mood thresholds for image selection |
| [personas.md](./personas.md) | Image paths per persona |
| [llm-integration.md](./llm-integration.md) | Source of message text |
| [system-overview.md](./system-overview.md) | How popup fits in the system |
