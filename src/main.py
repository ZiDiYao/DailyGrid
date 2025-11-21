import threading
import pystray
from PIL import Image, ImageDraw
# This import now works because of Step 1
from ui import App

# Global variable
app = None


def create_icon_image():
    # (Your existing code for the blue square icon...)
    image = Image.new('RGB', (64, 64), color=(30, 144, 255))
    d = ImageDraw.Draw(image)
    d.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
    return image


def on_tray_open(icon, item):
    """Restores the window"""
    if app:
        # deiconify restores the window from hidden state
        app.after(0, app.deiconify)


def on_tray_quit(icon, item):
    """Actually quits the app"""
    icon.stop()  # Stop the tray icon loop
    if app:
        # Calls the new function we added in Step 2
        app.after(0, app.real_quit)


def run_tray_icon():
    image = create_icon_image()
    menu = pystray.Menu(
        pystray.MenuItem("Open DailyGrid", on_tray_open, default=True),
        pystray.MenuItem("Quit", on_tray_quit)
    )
    icon = pystray.Icon("DailyGrid", image, "DailyGrid Tracker", menu)
    icon.run()


if __name__ == "__main__":
    # 1. Start Tray in background thread
    tray_thread = threading.Thread(target=run_tray_icon, daemon=True)
    tray_thread.start()

    # 2. Start GUI in main thread
    app = App()

    # When X is clicked, run on_closing (which now only does .withdraw())
    app.protocol("WM_DELETE_WINDOW", app.on_closing)

    print("Program started. Minimize to tray enabled.")
    app.mainloop()