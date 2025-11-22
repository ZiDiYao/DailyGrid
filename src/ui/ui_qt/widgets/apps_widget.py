from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

# ❗ 修正 1：使用新的、更现代和数量更多的调色板 ❗
APP_COLORS = [
    "#61dafb",  # 浅蓝 (React blue)
    "#50fa7b",  # 亮绿 (Dracule Green)
    "#ff79c6",  # 粉色 (Dracule Pink)
    "#f1fa8c",  # 亮黄 (Dracule Yellow)
    "#bd93f9",  # 浅紫 (Dracule Purple)
    "#ffb86c",  # 浅橙 (Dracule Orange)
    "#8be9fd",  # 浅青 (Dracule Cyan)
    "#ff6e67",  # 浅红 (Dracule Red)
    "#bfd7ea",  # 淡蓝 (Light Blue)
    "#c9e4de",  # 薄荷绿 (Mint Green)
]


class AppRowWidget(QWidget):
    """
    单行：应用名 + 比例条 + 时间
    """
    clicked = Signal(str)

    def __init__(self, app_name: str, seconds: float, color: str, ratio: float, parent=None):
        super().__init__(parent)
        # 确保 AppRowWidget 自身是透明背景
        self.setStyleSheet("background: transparent;")

        self.app_name = app_name
        self.seconds = seconds
        self.base_color = QColor(color)
        self.ratio = max(0.05, min(ratio, 1.0))

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 6, 0, 6)
        row.setSpacing(12)

        # 左：应用名
        display_name = app_name.replace(".exe", "")
        self.lbl_name = QLabel(display_name)
        # 修正 1.1：确保纯文本，移除所有边框和背景，并移除 padding
        self.lbl_name.setStyleSheet(
            "color: #c9d1d9; font-size: 13px; border: none; background: transparent; padding: 0;")
        self.lbl_name.setFixedWidth(140)
        row.addWidget(self.lbl_name)

        # 中：条形背景
        self.bar_bg = QFrame()
        self.bar_bg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.bar_bg.setFixedHeight(6)
        # 修正 2.2：只保留背景色和圆角，明确 border: none，移除所有进度的视觉效果
        self.bar_bg.setStyleSheet("background-color: #11161c; border-radius: 3px; border: none;")

        bar_layout = QHBoxLayout(self.bar_bg)
        bar_layout.setContentsMargins(0, 0, 0, 0)

        self.bar = QFrame()
        self.bar.setFixedHeight(6)
        # 确保 self.bar 自身也没有 border/highlight
        self.bar.setStyleSheet(f"background-color: {color}; border-radius: 3px; border: none;")

        bar_layout.addWidget(self.bar)
        bar_layout.addStretch()

        row.addWidget(self.bar_bg, 1)

        # 右：时间
        minutes = int(round(seconds / 60))
        self.lbl_time = QLabel(f"{minutes}m")
        # 修正 1.2 & 3.1：确保时间标签纯文本，移除所有边框和背景，并增加右侧 padding
        self.lbl_time.setStyleSheet(
            "color: #8b949e; font-size: 12px; border: none; background: transparent; padding: 0 5px 0 0;")
        self.lbl_time.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_time.setFixedWidth(50)  # 稍微增加宽度以容纳 padding
        row.addWidget(self.lbl_time)

        self.setCursor(Qt.PointingHandCursor)

        self._update_bar_width()

    def _update_bar_width(self):
        total_w = max(0, self.bar_bg.width())
        bar_w = int(total_w * self.ratio)
        bar_w = max(4, bar_w)
        self.bar.setFixedWidth(bar_w)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_bar_width()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.app_name)
        super().mousePressEvent(event)


class AppsWidget(QFrame):
    """
    Top Apps Today 区块 (限制显示 Top 10，并修正垂直布局)
    """
    clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WallpaperCard")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        # 标题
        self.lbl_title = QLabel("Top Apps Today")
        self.lbl_title.setStyleSheet(
            "font-size: 15px; font-weight: 600; "
            "color: #c9d1d9; border: none; background: transparent;"
        )
        main_layout.addWidget(self.lbl_title)

        # 行容器
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 8, 0, 0)
        self.rows_layout.setSpacing(8)
        main_layout.addWidget(self.rows_container)

        # 保持 main_layout 底部无 stretch
        # main_layout.addStretch() # 这一行保持移除

        self.row_widgets: list[AppRowWidget] = []

    def clear_rows(self):
        for row in self.row_widgets:
            row.setParent(None)
        self.row_widgets.clear()

        while self.rows_layout.count():
            item = self.rows_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def update_data(self, apps_data):
        """
        apps_data: [(app_name, seconds), ...]
        """
        self.clear_rows()

        # 修正：只取 Top 10 的 App 来显示 (与 database limit=10 保持一致)
        apps_to_display = apps_data[:10]

        if not apps_to_display:
            empty = QLabel("No data for today.")
            empty.setStyleSheet("color: #8b949e; font-size: 13px;")
            self.rows_layout.addWidget(empty)

            # ❗ 修正：即使无数据，也要添加 stretch，确保“无数据”标签向上对齐 ❗
            self.rows_layout.addStretch()
            return

        max_sec = max(sec or 0 for _, sec in apps_to_display) or 1

        # 调整 max_sec 的计算，以保证最长条形图的视觉比例
        if max_sec > 0:
            visual_max_ratio_target = 0.6
            adjusted_max_sec = max_sec / visual_max_ratio_target
            max_sec = max(max_sec, adjusted_max_sec)

        for idx, (name, sec) in enumerate(apps_to_display):
            sec = sec or 0
            # 颜色直接从新的 APP_COLORS 中按索引取，实现循环
            color = APP_COLORS[idx % len(APP_COLORS)]
            ratio = sec / max_sec if max_sec > 0 else 0.0

            row = AppRowWidget(name, sec, color, ratio)
            row.clicked.connect(self.clicked.emit)

            self.rows_layout.addWidget(row)
            self.row_widgets.append(row)

        # ❗ 修正：在所有 App Rows 后面添加 stretch，将内容列表向上推，解决底部空白问题 ❗
        self.rows_layout.addStretch()