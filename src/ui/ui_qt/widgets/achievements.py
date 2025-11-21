from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


class AchievementsWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")  # 繼承現有的卡片樣式 (圓角、深色背景)

        # 使用水平佈局，讓成就一字排開
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)

        # --- 佔位符內容 (模擬 4 個待解鎖的成就) ---
        # 之後你可以把這裡換成真實的邏輯
        for i in range(1, 5):
            item = self.create_placeholder_item(f"Achievement {i}")
            self.layout.addWidget(item)

        self.layout.addStretch()  # 彈簧，把內容頂到左邊

    def create_placeholder_item(self, text):
        """創建一個單個成就的佔位 UI"""
        container = QFrame()
        container.setStyleSheet("background-color: transparent;")
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(8)

        # 1. 圖標 (用 Emoji 暫代，或者你可以畫圓圈)
        icon = QLabel("🔒")
        icon.setAlignment(Qt.AlignCenter)
        # 弄一個灰色的圓形背景
        icon.setStyleSheet("""
            QLabel {
                font-size: 24px;
                background-color: #21262d;
                border-radius: 25px; /* 半徑是寬度的一半 -> 圓形 */
                color: #8b949e;
                min-width: 50px;
                min-height: 50px;
                max-width: 50px;
                max-height: 50px;
            }
        """)

        # 2. 文字
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #8b949e; font-size: 12px;")

        v_layout.addWidget(icon, 0, Qt.AlignCenter)
        v_layout.addWidget(label, 0, Qt.AlignCenter)

        return container