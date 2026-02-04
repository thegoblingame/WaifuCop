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
| Framework | tkinter |
| Window Type | Toplevel (borderless) |
| Default Size | 750 x 450 pixels |
| Position | Centered on screen |
| Always on Top | Yes |
| Resizable | No |

### 2.2 Window Behavior

```python
# Window configuration
root.overrideredirect(True)  # Remove window border/title bar
root.attributes("-topmost", True)  # Always on top
root.resizable(False, False)  # Fixed size

# Center on screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - 750) // 2
y = (screen_height - 450) // 2
root.geometry(f"750x450+{x}+{y}")
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
| Close Button (Normal) | Transparent | - |
| Close Button (Hover) | Red | `#FF0000` |
| Close Button (Disabled) | Gray | `#666666` |

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

| Component | Width | Height | Position |
|-----------|-------|--------|----------|
| Header Bar | 750px | 30px | Top |
| Waifu Image Area | ~300px | ~400px | Left side |
| Message Area | ~400px | ~350px | Right side |
| Waifu Meter Display | ~100px | ~40px | Bottom-right |

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

Images are scaled to fit the allocated area while maintaining aspect ratio:

```python
from PIL import Image, ImageTk

def load_and_scale_image(path: str, max_width: int, max_height: int):
    img = Image.open(path)

    # Calculate scale to fit within bounds
    width_ratio = max_width / img.width
    height_ratio = max_height / img.height
    scale = min(width_ratio, height_ratio)

    new_width = int(img.width * scale)
    new_height = int(img.height * scale)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)
```

---

## 5. Text Display

### 5.1 Typewriter Effect

The message is displayed character-by-character to create engagement:

```python
def typewriter_effect(label: tk.Label, text: str, delay_ms: int = 20):
    """Display text one character at a time."""

    def type_next(index: int):
        if index <= len(text):
            label.config(text=text[:index])
            label.after(delay_ms, lambda: type_next(index + 1))
        else:
            # Typing complete - signal that window can now auto-close
            typing_complete.set(True)

    type_next(0)
```

### 5.2 Text Styling

| Property | Value |
|----------|-------|
| Font Family | System default (or configurable) |
| Font Size | 12-14pt |
| Color | White (`#FFFFFF`) |
| Wrapping | Word wrap at container width |
| Alignment | Left-aligned |

---

## 6. Close Button Behavior

### 6.1 Delayed Enable

The close button is disabled for the first 3 seconds to ensure the user sees the message:

```python
def setup_close_button(button: tk.Button, root: tk.Tk):
    button.config(state="disabled", fg="#666666")

    def enable_close():
        button.config(state="normal", fg="#FFFFFF")
        # Add hover effect
        button.bind("<Enter>", lambda e: button.config(bg="#FF0000"))
        button.bind("<Leave>", lambda e: button.config(bg="#0078d4"))

    root.after(3000, enable_close)  # Enable after 3 seconds
```

### 6.2 Hover Effect

When enabled, the close button shows visual feedback on hover:
- Normal: Transparent/header color
- Hover: Red background (`#FF0000`)

---

## 7. Window Lifecycle

### 7.1 Auto-Close Logic

The window closes automatically when BOTH conditions are met:
1. Minimum display time has elapsed (30 seconds)
2. Typewriter effect has completed

```python
def setup_auto_close(root: tk.Tk, duration_ms: int = 30000):
    typing_complete = tk.BooleanVar(value=False)
    timer_complete = tk.BooleanVar(value=False)

    def check_close():
        if typing_complete.get() and timer_complete.get():
            root.destroy()
        else:
            root.after(100, check_close)

    def timer_done():
        timer_complete.set(True)

    root.after(duration_ms, timer_done)
    root.after(100, check_close)

    return typing_complete  # Return so typewriter can signal completion
```

### 7.2 Manual Close

User can close the window after the 3-second delay by:
- Clicking the close button
- (Future: Pressing Escape key)

---

## 8. Waifu Meter Display

### 8.1 Visual Representation

The current waifu meter is displayed in the bottom-right corner:

```
┌──────────────────┐
│   Waifu Meter    │
│       67         │
└──────────────────┘
```

### 8.2 Color Coding (Optional Enhancement)

| Meter Range | Color |
|-------------|-------|
| 0-30 | Red |
| 31-70 | Yellow |
| 71-100 | Green |

---

## 9. Parameters

### 9.1 Function Signature

```python
def show_popup(
    img_path: str,
    message: str,
    waifu_meter: int = 50,
    duration_ms: int = 30000
) -> None:
    """
    Display the waifu popup window.

    Args:
        img_path: Path to the waifu image file
        message: LLM-generated message to display
        waifu_meter: Current meter score (0-100)
        duration_ms: Minimum display time before auto-close
    """
```

### 9.2 Command-Line Interface

For testing and external invocation:

```bash
python waifu_popup.py <image_path> <message> [waifu_meter] [duration_ms]
```

---

## 10. Error Handling

### 10.1 Missing Image

If the specified image file doesn't exist:
- Log warning
- Use a fallback/default image
- Do not crash

```python
def safe_load_image(path: str, fallback_path: str):
    try:
        return load_and_scale_image(path, MAX_WIDTH, MAX_HEIGHT)
    except FileNotFoundError:
        print(f"Warning: Image not found: {path}")
        return load_and_scale_image(fallback_path, MAX_WIDTH, MAX_HEIGHT)
```

### 10.2 Display Errors

If tkinter fails to create the window:
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

- [ ] Window creation with borderless/topmost settings
- [ ] Header bar with title and close button
- [ ] Image loading and scaling
- [ ] Image selection based on waifu meter
- [ ] Typewriter effect for message
- [ ] 3-second close button delay
- [ ] Hover effect on close button
- [ ] Auto-close after 30 seconds + typing complete
- [ ] Waifu meter display
- [ ] Command-line interface for testing
- [ ] Error handling for missing images

---

## 13. Related Specifications

| Spec | Relevance |
|------|-----------|
| [waifu-meter.md](./waifu-meter.md) | Mood thresholds for image selection |
| [personas.md](./personas.md) | Image paths per persona |
| [llm-integration.md](./llm-integration.md) | Source of message text |
| [system-overview.md](./system-overview.md) | How popup fits in the system |
