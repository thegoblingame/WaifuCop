import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk


def show_waifu_popup(
    img_path: str,
    message: str,
    title: str = "waifucop",
    width: int | None = 750,
    height: int | None = 450,
    duration_ms: int = 30000,
) -> None:

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    bg_color = "#333333"
    header_color = "#0078d4"
    root.configure(bg=bg_color)

    # ------------------------------------------------------------
    # drag handling
    drag = {"x": 0, "y": 0}

    def start_move(event):
        drag["x"] = event.x
        drag["y"] = event.y

    def do_move(event):
        root.geometry(f"+{event.x_root - drag['x']}+{event.y_root - drag['y']}")
    # ------------------------------------------------------------

    # load + scale image
    img = Image.open(img_path)
    if height:
        target_h = height - 70
        scale = target_h / img.height
        img = img.resize((int(img.width * scale), target_h), Image.LANCZOS)
    tk_img = ImageTk.PhotoImage(img)

    img_w, img_h = img.size
    if width is None:
        width = img_w + 260
    if height is None:
        height = max(img_h + 60, 220)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(
        f"{width}x{height}+{(screen_w - width)//2}+{(screen_h - height)//3}"
    )

    # ===================== HEADER BAR ===========================
    header = tk.Frame(root, bg=header_color, height=30)
    header.pack(fill="x")

    header.bind("<ButtonPress-1>", start_move)
    header.bind("<B1-Motion>", do_move)

    title_label = tk.Label(
        header,
        text=title,
        bg=header_color,
        fg="#ffffff",
        font=("Allerta", 16, "bold"),
    )
    title_label.pack(side="left", padx=10)

    def close():
        root.destroy()

    def on_enter(_):
        close_btn.config(bg="#c42b1c")  # windows-style red

    def on_leave(_):
        close_btn.config(bg=header_color)

    close_btn = tk.Button(
        header,
        text="✕",
        command=close,
        bg=header_color,
        fg="white",
        bd=0,
        padx=10,
        pady=2,
        font=("Allerta", 16, "bold"),
        activebackground="#c42b1c",
        activeforeground="white",
    )

    close_btn.bind("<Enter>", on_enter)
    close_btn.bind("<Leave>", on_leave)
    close_btn.pack(side="right")

    # ===================== BODY ================================
    frame = tk.Frame(root, bg=bg_color)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    frame.bind("<ButtonPress-1>", start_move)
    frame.bind("<B1-Motion>", do_move)
    root.bind("<ButtonPress-1>", start_move)
    root.bind("<B1-Motion>", do_move)

    img_label = tk.Label(frame, image=tk_img, bg=bg_color)
    img_label.image = tk_img
    img_label.pack(side="left", padx=(0, 10))

    img_label.bind("<ButtonPress-1>", start_move)
    img_label.bind("<B1-Motion>", do_move)

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

    # ===================== TYPEWRITER EFFECT ===================
    typing_delay_ms = 20  # smaller = faster typing

    def type_writer(index: int = 0):
        if index <= len(message):
            text_label.config(text=message[:index])
            root.after(typing_delay_ms, type_writer, index + 1)

    type_writer()

    # make sure it doesn't close before the text is done typing
    if duration_ms > 0:
        total_typing_time = typing_delay_ms * len(message)
        close_after = max(duration_ms, total_typing_time + 1000)
        root.after(close_after, close)

    root.mainloop()


if __name__ == "__main__":
    show_waifu_popup(sys.argv[1], sys.argv[2])
