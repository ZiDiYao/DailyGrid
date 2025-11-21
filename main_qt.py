import sys
import os

# 确保能找到 src 包
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from src.ui.ui_qt import MainWindow

if __name__ == "__main__":
    # 高分屏支持
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)

    # 防止关闭最后一个窗口时程序直接退出（因为我们要用托盘）
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())