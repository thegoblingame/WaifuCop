import sys
from pathlib import Path

from PySide6.QtWidgets import (
	QApplication,
	QHBoxLayout,
	QLabel,
	QVBoxLayout,
	QWidget,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFontDatabase, QFont, QPixmap

PROJECT_ROOT = Path(__file__).resolve().parent.parent

with open(PROJECT_ROOT / "debug.txt", "a") as f:
	f.write(str(sys.argv) + "\n")


def _load_font() -> str:
	"""Load Allerta font and return the family name."""
	font_path = str(PROJECT_ROOT / "fonts" / "Allerta-Regular.ttf")
	font_id = QFontDatabase.addApplicationFont(font_path)
	if font_id >= 0:
		families = QFontDatabase.applicationFontFamilies(font_id)
		if families:
			return families[0]
	return "Allerta"


class CloseButton(QLabel):
	"""Close button label with hover/click behavior and delayed enable."""

	def __init__(self, close_callback):
		super().__init__("✕")
		self._close_callback = close_callback
		self._enabled = False
		self._header_color = "#0078d4"
		self._hover_color = "#c42b1c"

		self.setAlignment(Qt.AlignCenter)
		self.setFixedSize(30, 30)
		self.setCursor(Qt.ArrowCursor)
		self._apply_style(self._header_color, "#888888")

	def enable(self):
		self._enabled = True
		self.setCursor(Qt.PointingHandCursor)
		self._apply_style(self._header_color, "white")

	def _apply_style(self, bg: str, fg: str):
		self.setStyleSheet(f"background-color: {bg}; color: {fg};")

	def enterEvent(self, event):
		if self._enabled:
			self._apply_style(self._hover_color, "white")
		super().enterEvent(event)

	def leaveEvent(self, event):
		if self._enabled:
			self._apply_style(self._header_color, "white")
		super().leaveEvent(event)

	def mousePressEvent(self, event):
		if self._enabled and event.button() == Qt.LeftButton:
			self._close_callback()
		super().mousePressEvent(event)


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
		width_pct: Window width as a fraction of screen width (0.0-1.0)
		height_pct: Window height as a fraction of screen height (0.0-1.0)
		duration_ms: Minimum display time before auto-close (0 to disable)
	"""
	app = QApplication.instance() or QApplication(sys.argv)

	font_family = _load_font()
	body_font = QFont(font_family, 16)
	header_font = QFont(font_family, 16)
	header_font.setBold(True)
	score_font = QFont(font_family, 12)

	bg_color = "#333333"
	header_color = "#0078d4"

	# ===================== WINDOW SETUP ===========================
	screen = app.primaryScreen().geometry()
	screen_w, screen_h = screen.width(), screen.height()
	width = int(screen_w * width_pct)
	height = int(screen_h * height_pct)

	window = QWidget()
	window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
	window.setFixedSize(width, height)
	window.move((screen_w - width) // 2, (screen_h - height) // 3)
	window.setStyleSheet(f"background-color: {bg_color};")

	main_layout = QVBoxLayout(window)
	main_layout.setContentsMargins(0, 0, 0, 0)
	main_layout.setSpacing(0)

	# ===================== TIMERS =================================
	typing_timer = QTimer()
	typing_timer.setInterval(20)

	def close():
		typing_timer.stop()
		window.close()

	# ===================== HEADER BAR =============================
	header = QWidget()
	header.setFixedHeight(30)
	header.setStyleSheet(f"background-color: {header_color};")

	header_layout = QHBoxLayout(header)
	header_layout.setContentsMargins(10, 0, 0, 0)
	header_layout.setSpacing(0)

	title_label = QLabel(title)
	title_label.setFont(header_font)
	title_label.setStyleSheet(f"color: white; background-color: {header_color};")
	header_layout.addWidget(title_label)

	header_layout.addStretch()

	close_btn = CloseButton(close)
	close_btn.setFont(header_font)
	header_layout.addWidget(close_btn)

	QTimer.singleShot(3000, close_btn.enable)

	main_layout.addWidget(header)

	# ===================== BODY ===================================
	body = QWidget()
	body.setStyleSheet(f"background-color: {bg_color};")
	body_layout = QHBoxLayout(body)
	body_layout.setContentsMargins(10, 10, 10, 10)
	body_layout.setSpacing(10)

	# --- Image ---
	target_h = height - 70
	pixmap = QPixmap(img_path)
	if pixmap.isNull():
		print(f"Warning: Image not found or failed to load: {img_path}")
	else:
		pixmap = pixmap.scaledToHeight(target_h, Qt.SmoothTransformation)

	img_label = QLabel()
	img_label.setPixmap(pixmap)
	img_label.setAlignment(Qt.AlignTop)
	img_label.setStyleSheet(f"background-color: {bg_color};")
	body_layout.addWidget(img_label)

	img_w = pixmap.width() if not pixmap.isNull() else 0

	# --- Text area (message + meter) ---
	text_container = QWidget()
	text_container.setStyleSheet(f"background-color: {bg_color};")
	text_layout = QVBoxLayout(text_container)
	text_layout.setContentsMargins(0, 0, 0, 0)
	text_layout.setSpacing(0)

	wrap_width = width - img_w - 60
	text_label = QLabel("")
	text_label.setFont(body_font)
	text_label.setStyleSheet(f"color: white; background-color: {bg_color};")
	text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
	text_label.setWordWrap(True)
	text_label.setFixedWidth(max(wrap_width, 100))
	text_layout.addWidget(text_label)

	text_layout.addStretch()

	# --- Waifu meter score ---
	if waifu_meter is not None:
		score_label = QLabel(str(waifu_meter))
		score_label.setFont(score_font)
		score_label.setStyleSheet(f"color: #888888; background-color: {bg_color};")
		score_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
		text_layout.addWidget(score_label)

	body_layout.addWidget(text_container)

	main_layout.addWidget(body, 1)

	# ===================== TYPEWRITER EFFECT =======================
	typing_index = [0]

	def type_writer():
		if not window.isVisible():
			typing_timer.stop()
			return
		if typing_index[0] <= len(message):
			text_label.setText(message[:typing_index[0]])
			typing_index[0] += 1
		else:
			typing_timer.stop()

	typing_timer.timeout.connect(type_writer)
	typing_timer.start()

	# ===================== AUTO-CLOSE =============================
	if duration_ms > 0:
		typing_delay_ms = 20
		total_typing_time = typing_delay_ms * len(message)
		close_after = max(duration_ms, total_typing_time + 1000)
		QTimer.singleShot(close_after, close)

	# ===================== SHOW ===================================
	window.show()
	app.exec()


if __name__ == "__main__":
	show_waifu_popup(sys.argv[1], sys.argv[2], int(sys.argv[3]))
