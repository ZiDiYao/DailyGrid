# 文件路径: monitor/idle_check.py
import ctypes
from ctypes import Structure, c_uint, sizeof, byref


# 定义 Windows API 需要的结构体
class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint)
    ]


def get_idle_duration() -> float:
    """
    调用 Windows API 获取系统闲置时间（秒）。
    Returns:
        float: 距离上一次用户输入的秒数。
    """
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(LASTINPUTINFO)

    # 调用 User32.dll
    if ctypes.windll.user32.GetLastInputInfo(byref(lastInputInfo)):
        # GetTickCount() 返回系统启动后的毫秒数
        millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return millis / 1000.0

    return 0.0