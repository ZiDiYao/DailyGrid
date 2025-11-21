import platform
import matplotlib.pyplot as plt
import customtkinter as ctk

# --- 1. 字体设置 ---
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Segoe UI']
elif system_name == "Darwin":
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC']
plt.rcParams['axes.unicode_minus'] = False

# --- 2. 颜色常量 ---
GH_BG = "#0d1117"
GH_FRAME = "#161b22"
GH_TEXT_MAIN = "#c9d1d9"
GH_TEXT_SUB = "#8b949e"
GH_BLUE = "#1f6feb"
GH_HOVER = "#30363d"
GH_CARD_HOVER = "#21262d"

COLOR_SCREEN_TIME = "#238636"
COLOR_CLICKS = "#1f6feb"
COLOR_KEYS = "#d29922"

IOS_TRACK_COLOR = "#010409"
APP_COLORS = ['#1f6feb', '#238636', '#d29922', '#8957e5', '#da3633']
TT_BG_NORMAL = "#1f2328"
TT_BG_HIGHLIGHT = "#40464d"

# --- 3. 尺寸与字体 ---
PILL_RADIUS = 20
TOOLTIP_FONT = ("Segoe UI", 11)
MAIN_FONT = ("Segoe UI", 12)
NUM_FONT = ("Segoe UI", 24, "bold")

# --- 4. 初始化主题 ---
def setup_theme():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")