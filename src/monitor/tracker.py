from pynput import mouse, keyboard
import threading


class InputListener:
    def __init__(self):
        self._mouse_clicks = 0
        self._keystrokes = 0
        self._key_details = {}
        self._lock = threading.Lock()

        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.key_listener = keyboard.Listener(on_press=self._on_press)

    def start(self):
        self.mouse_listener.start()
        self.key_listener.start()
        print("Input listeners started.")

    def stop(self):
        self.mouse_listener.stop()
        self.key_listener.stop()

    def _on_click(self, x, y, button, pressed):
        if pressed:
            with self._lock:
                self._mouse_clicks += 1

    def _on_press(self, key):
        with self._lock:
            self._keystrokes += 1
            key_name = ""
            try:
                if hasattr(key, 'char') and key.char:
                    key_name = key.char.upper()
                else:
                    key_name = str(key).replace("Key.", "").upper()
            except:
                key_name = "UNKNOWN"

            if key_name:
                self._key_details[key_name] = self._key_details.get(key_name, 0) + 1

    def get_and_reset_counts(self):
        """供 MonitorService 调用：获取并清空"""
        with self._lock:
            clicks = self._mouse_clicks
            keys = self._keystrokes
            details = self._key_details.copy()

            self._mouse_clicks = 0
            self._keystrokes = 0
            self._key_details = {}

        return clicks, keys, details

    # --- 新增：只获取当前内存中的增量 (不清空) ---
    def get_current_counts(self):
        """供 UI 高频调用：只读，不写"""
        with self._lock:
            return self._mouse_clicks, self._keystrokes