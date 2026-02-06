import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from PIL import Image, ImageTk

# Get the project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

with open(PROJECT_ROOT / "debug.txt", "a") as f:
    f.write(str(sys.argv) + "\n")

def show_waifu_popup(
    img_path: str,
    message: str,
    waifu_meter: int | None = 50,
    title: str = "waifucop",
    width_pct: float = 0.40,   # percentage of screen width (0.0 to 1.0)
    height_pct: float = 0.45,  # percentage of screen height (0.0 to 1.0)
    duration_ms: int = 30000,
) -> None:

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    bg_color = "#333333"
    header_color = "#0078d4"
    root.configure(bg=bg_color)

    # Get screen dimensions first to calculate percentage-based sizes
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    width = int(screen_w * width_pct)
    height = int(screen_h * height_pct)

    # load + scale image
    img = Image.open(img_path)
    target_h = height - 70
    scale = target_h / img.height
    img = img.resize((int(img.width * scale), target_h), Image.LANCZOS)
    tk_img = ImageTk.PhotoImage(img)

    img_w, img_h = img.size

    root.geometry(
        f"{width}x{height}+{(screen_w - width)//2}+{(screen_h - height)//3}"
    )

    # ===================== HEADER BAR ===========================
    header = tk.Frame(root, bg=header_color, height=30)
    header.pack(fill="x")

    title_label = tk.Label(
        header,
        text=title,
        bg=header_color,
        fg="#ffffff",
        font=("Allerta", 16, "bold"),
    )
    title_label.pack(side="left", padx=10)

    # ids for tk.after so we can cancel them
    typing_job_id = None
    close_job_id = None

    def close():
        nonlocal typing_job_id, close_job_id
        # cancel scheduled callbacks if they exist
        try:
            if typing_job_id is not None:
                root.after_cancel(typing_job_id)
        except Exception:
            pass
        try:
            if close_job_id is not None:
                root.after_cancel(close_job_id)
        except Exception:
            pass
        root.destroy()

    # Track whether close button hover effects are enabled
    close_btn_enabled = {"value": False}

    def on_enter(_):
        if close_btn_enabled["value"]:
            close_btn.config(bg="#c42b1c")  # windows-style red

    def on_leave(_):
        if close_btn_enabled["value"]:
            close_btn.config(bg=header_color)

    def on_click(_):
        if close_btn_enabled["value"]:
            close()

    # Use Label instead of Button for cross-platform color support
    close_btn = tk.Label(
        header,
        text="✕",
        bg=header_color,
        fg="#888888",  # Greyed out initially
        padx=10,
        pady=2,
        font=("Allerta", 16, "bold"),
        cursor="arrow",
    )

    close_btn.bind("<Enter>", on_enter)
    close_btn.bind("<Leave>", on_leave)
    close_btn.bind("<Button-1>", on_click)
    close_btn.pack(side="right")

    # Enable close button after 3 seconds
    def enable_close_btn():
        if root.winfo_exists():
            close_btn_enabled["value"] = True
            close_btn.config(fg="white", cursor="hand2")

    root.after(3000, enable_close_btn)

    # ===================== BODY ================================
    frame = tk.Frame(root, bg=bg_color)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    img_label = tk.Label(frame, image=tk_img, bg=bg_color)
    img_label.image = tk_img
    img_label.pack(side="left", padx=(0, 10))

    # start with empty text, we’ll type it in
    text_label = tk.Label(
        frame,
        text="",
        bg=bg_color,
        fg="#ffffff",
        justify="left",
        anchor="nw",
        wraplength=width - img_w - 60,
        font=("Allerta", 16),
    )
    text_label.pack(side="right", fill="both", expand=True)

    # ===================== SCORE DISPLAY =======================
    if waifu_meter is not None:
        score_label = tk.Label(
            root,
            text=str(waifu_meter),
            bg=bg_color,
            fg="#888888",
            font=("Allerta", 12),
            anchor="se",
        )
        score_label.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")

    # ===================== TYPEWRITER EFFECT ===================
    typing_delay_ms = 20  # smaller = faster typing

    def type_writer(index: int = 0):
        nonlocal typing_job_id
        # if the window is gone, don't schedule anything
        if not root.winfo_exists():
            return
        if index <= len(message):
            text_label.config(text=message[:index])
            typing_job_id = root.after(typing_delay_ms, type_writer, index + 1)

    type_writer()

    # make sure it doesn't close before the text is done typing
    if duration_ms > 0:
        total_typing_time = typing_delay_ms * len(message)
        close_after = max(duration_ms, total_typing_time + 1000)
        close_job_id = root.after(close_after, close)

    root.mainloop()

if __name__ == "__main__":
    show_waifu_popup(sys.argv[1], sys.argv[2], sys.argv[3])