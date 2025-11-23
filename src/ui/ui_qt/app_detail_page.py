from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt, Signal


class AppDetailPage(QWidget):
    """
    应用详情页
    """
    # 定义一个返回信号，供 MainWindow 切换回主页使用
    back_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AppDetailPage")

        # 简单的布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 顶部导航栏（返回按钮 + 标题）
        nav_layout = QHBoxLayout()

        self.btn_back = QPushButton("← Back")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8b949e;
                border: none;
                font-size: 14px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                color: #58a6ff;
            }
        """)
        self.btn_back.clicked.connect(self.back_clicked.emit)

        nav_layout.addWidget(self.btn_back)
        nav_layout.addStretch()  # 弹簧，把按钮顶在左边

        layout.addLayout(nav_layout)

        # 详情内容占位符
        self.lbl_title = QLabel("App Detail")
        self.lbl_title.setStyleSheet("color: #c9d1d9; font-size: 24px; font-weight: bold;")
        layout.addWidget(self.lbl_title)

        self.lbl_content = QLabel("Select an app to view details.")
        self.lbl_content.setStyleSheet("color: #8b949e; font-size: 14px;")
        layout.addWidget(self.lbl_content)

        layout.addStretch()

    def set_app_data(self, app_name: str):
        """
        用于接收外部传入的数据并更新界面
        """
        self.lbl_title.setText(app_name)
        self.lbl_content.setText(f"Details for {app_name} will be shown here.")