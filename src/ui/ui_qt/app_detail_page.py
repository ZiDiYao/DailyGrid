from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, Signal


class AppDetailPage(QWidget):
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        # --- 导航栏 ---
        nav_layout = QHBoxLayout()
        self.btn_back = QPushButton("← Back")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setFixedWidth(80)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #161b22; border: 1px solid #30363d; color: #c9d1d9; border-radius: 6px; padding: 5px;
            }
            QPushButton:hover { background-color: #30363d; }
        """)
        self.btn_back.clicked.connect(self.back_clicked.emit)

        nav_layout.addWidget(self.btn_back)
        nav_layout.addStretch()

        self.layout.addLayout(nav_layout)

        # --- 标题 ---
        self.lbl_title = QLabel("App Usage Analytics")
        self.lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #c9d1d9;")
        self.layout.addWidget(self.lbl_title)

        # --- 占位内容 ---
        self.lbl_placeholder = QLabel("More detailed app charts will go here.")
        self.lbl_placeholder.setStyleSheet("color: #8b949e; font-size: 14px;")
        self.lbl_placeholder.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.lbl_placeholder)

        self.layout.addStretch()