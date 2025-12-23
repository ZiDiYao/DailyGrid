from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

APP_COLORS = [
    "#38bdf8",  # 1. Sky Blue (明亮的主蓝)
    "#818cf8",  # 2. Indigo (专业的靛蓝)
    "#c084fc",  # 3. Soft Purple (柔和紫)
    "#2dd4bf",  # 4. Teal (科技青)
    "#60a5fa",  # 5. Blue (标准蓝)
    "#94a3b8",  # 6. Slate (低调的灰蓝)
    "#a78bfa",  # 7. Violet (浅紫)
    "#5eead4",  # 8. Cyan (青色)
    "#475569",  # 9. Dark Slate (深岩灰 - 用于排名靠后的)
    "#64748b",  # 10. Slate Grey
]


def format_duration_precise(seconds: float) -> str:
    if seconds <= 0: return "0s"
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m"
    else:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"


def clean_app_name(raw_name: str) -> str:
    if not raw_name: return "Unknown"
    return raw_name.replace(".exe", "").replace(".EXE", "")


class AppRowWidget(QWidget):
    clicked = Signal(str)

    def __init__(self, app_name: str, seconds: float, color: str, ratio: float, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        self.app_name = app_name
        self.ratio = max(0.01, min(ratio, 1.0))

        # 布局
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(12)

        # 1. Name
        self.lbl_name = QLabel(clean_app_name(app_name))
        # 稍微调亮一点字体颜色，增加对比度
        self.lbl_name.setStyleSheet("color: #e6edf3; font-size: 13px; font-weight: 500;")
        self.lbl_name.setFixedWidth(120)
        row.addWidget(self.lbl_name)

        # 2. Bar Container
        self.bar_container = QWidget()
        self.bar_container.setFixedHeight(6)
        self.bar_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        bar_layout = QHBoxLayout(self.bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)

        self.bar = QFrame()
        self.bar.setFixedHeight(6)
        # 使用传入的 color
        self.bar.setStyleSheet(f"background-color: {color}; border-radius: 3px;")

        bar_layout.addWidget(self.bar)
        bar_layout.addStretch()
        row.addWidget(self.bar_container, 1)

        # 3. Time
        self.lbl_time = QLabel(format_duration_precise(seconds))
        # 时间颜色稍微调暗，突出主体
        self.lbl_time.setStyleSheet("color: #7d8590; font-size: 12px; font-family: 'Segoe UI';")
        self.lbl_time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_time.setFixedWidth(55)
        row.addWidget(self.lbl_time)

        self.setCursor(Qt.PointingHandCursor)
        self._update_bar_width()

    def _update_bar_width(self):
        total_w = self.bar_container.width()
        if total_w > 0:
            bar_w = int(total_w * self.ratio)
            self.bar.setFixedWidth(max(4, bar_w))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_bar_width()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.app_name)
        super().mousePressEvent(event)


class AppsWidget(QFrame):
    clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")

        # 保护布局不被挤压
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # 标题
        self.lbl_title = QLabel("Top Apps Today")
        self.lbl_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #f0f6fc; margin-bottom: 4px;")
        layout.addWidget(self.lbl_title)

        # 列表容器
        self.rows_container = QWidget()
        self.rows_container.setStyleSheet("background: transparent;")
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(2)

        layout.addWidget(self.rows_container)
        layout.addStretch()

    def update_data(self, apps_data):
        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not apps_data:
            empty = QLabel("No activity yet")
            empty.setStyleSheet("color: #7d8590; font-style: italic;")
            self.rows_layout.addWidget(empty)
            return

        top_apps = apps_data[:8]
        max_sec = max(sec for _, sec in top_apps) if top_apps else 1

        for idx, (name, sec) in enumerate(top_apps):
            # 循环使用我们定义好的冷色调配色
            color = APP_COLORS[idx % len(APP_COLORS)]
            ratio = sec / max_sec

            row = AppRowWidget(name, sec, color, ratio)
            row.clicked.connect(self.clicked.emit)
            self.rows_layout.addWidget(row)