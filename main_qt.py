import sys
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

# 确保能找到 src 包
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from src.ui.ui_qt import MainWindow

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

# ... 其他 import ...

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ---------------------------------------------------------
    # 🎨 字体美化核心代码
    # ---------------------------------------------------------
    # 1. 设置优先字体族：英文优先 Segoe UI (Win10/11标准)，中文优先微软雅黑
    font = QFont("Segoe UI")
    font.setFamilies(["Segoe UI", "Microsoft YaHei", "PingFang SC", "sans-serif"])

    # 2. 设置基础字号 (通常 9pt 或 10pt 适合桌面端)
    font.setPointSize(10)

    # 3. 开启字体抗锯齿 (这一步非常重要，拒绝锯齿)
    font.setStyleStrategy(QFont.PreferAntialias)

    # 4. 甚至可以微调字体的 Hinting 策略，让它在液晶屏上更清晰
    font.setHintingPreference(QFont.PreferNoHinting)

    # 应用到全局
    app.setFont(font)
    # ---------------------------------------------------------

    window = MainWindow()
    window.show()

    sys.exit(app.exec())