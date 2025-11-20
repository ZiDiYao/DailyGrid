import threading
from PIL import Image, ImageDraw
import pystray
from ui.app import App

# 全局变量，用于在不同线程间访问
app = None


def create_icon_image():
    """
    生成一个临时的图标图片（蓝色方块），这样你就不用去找 icon.png 了。
    如果你有自己的图标，可以使用 Image.open('icon.png')
    """
    # 创建一个 64x64 的图片
    image = Image.new('RGB', (64, 64), color=(30, 144, 255))
    d = ImageDraw.Draw(image)
    # 画一个简单的网格图案代表 DailyGrid
    d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
    return image


def on_tray_open(icon, item):
    """点击托盘菜单的 '打开'"""
    # 必须在主线程中操作 UI，所以使用 after
    if app:
        app.after(0, app.deiconify)


def on_tray_quit(icon, item):
    """点击托盘菜单的 '退出'"""
    icon.stop()  # 停止托盘循环
    if app:
        # 调用我们在 ui/app.py 里新写的 real_quit
        app.after(0, app.real_quit)


def run_tray_icon():
    """在独立线程中运行系统托盘"""
    image = create_icon_image()

    # 定义右键菜单
    menu = pystray.Menu(
        pystray.MenuItem("Open DailyGrid", on_tray_open, default=True),  # default=True 允许双击打开
        pystray.MenuItem("Quit", on_tray_quit)
    )

    icon = pystray.Icon("DailyGrid", image, "DailyGrid Tracker", menu)
    icon.run()


if __name__ == "__main__":
    # 1. 启动系统托盘 (在子线程运行，否则会阻塞 UI)
    tray_thread = threading.Thread(target=run_tray_icon, daemon=True)
    tray_thread.start()

    # 2. 启动主程序 UI
    app = App()

    # 绑定窗口关闭事件 (点击 X -> 隐藏)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)

    print("程序已启动。点击窗口的 X 将最小化到托盘。")
    print("在右下角托盘区右键图标可完全退出。")

    app.mainloop()