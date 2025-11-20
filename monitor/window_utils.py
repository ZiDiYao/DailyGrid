# monitor/window_utils.py
import win32gui
import win32process
import psutil


def get_active_process_name():
    """
    获取当前前台窗口的进程名 (例如 'chrome.exe')
    """
    try:
        # 1. 获取当前活动窗口的句柄
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None

        # 2. 获取窗口对应的进程 ID (PID)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        if not pid:
            return None

        # 3. 通过 PID 获取进程名
        process = psutil.Process(pid)
        name = process.name()
        return name
    except Exception:
        # 可能会遇到权限问题或窗口刚关闭
        return None