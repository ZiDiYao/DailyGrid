import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors

# 键盘布局 (Label, X, Y, Width)
# 修复：将特殊符号改为普通文本，防止字体缺失警告
KEYBOARD_LAYOUT = [
    # Row 1
    ('ESC', 0, 4, 1), ('1', 1, 4, 1), ('2', 2, 4, 1), ('3', 3, 4, 1), ('4', 4, 4, 1),
    ('5', 5, 4, 1), ('6', 6, 4, 1), ('7', 7, 4, 1), ('8', 8, 4, 1), ('9', 9, 4, 1), ('0', 10, 4, 1),
    ('-', 11, 4, 1), ('=', 12, 4, 1), ('Back', 13, 4, 2),  # 改为 Back

    # Row 2
    ('TAB', 0, 3, 1.5), ('Q', 1.5, 3, 1), ('W', 2.5, 3, 1), ('E', 3.5, 3, 1), ('R', 4.5, 3, 1),
    ('T', 5.5, 3, 1), ('Y', 6.5, 3, 1), ('U', 7.5, 3, 1), ('I', 8.5, 3, 1), ('O', 9.5, 3, 1),
    ('P', 10.5, 3, 1), ('[', 11.5, 3, 1), (']', 12.5, 3, 1), ('\\', 13.5, 3, 1.5),

    # Row 3
    ('CAPS', 0, 2, 1.75), ('A', 1.75, 2, 1), ('S', 2.75, 2, 1), ('D', 3.75, 2, 1), ('F', 4.75, 2, 1),
    ('G', 5.75, 2, 1), ('H', 6.75, 2, 1), ('J', 7.75, 2, 1), ('K', 8.75, 2, 1), ('L', 9.75, 2, 1),
    (';', 10.75, 2, 1), ("'", 11.75, 2, 1), ('Enter', 12.75, 2, 2.25),  # 改为 Enter

    # Row 4
    ('Shift', 0, 1, 2.25), ('Z', 2.25, 1, 1), ('X', 3.25, 1, 1), ('C', 4.25, 1, 1), ('V', 5.25, 1, 1),  # 改为 Shift
    ('B', 6.25, 1, 1), ('N', 7.25, 1, 1), ('M', 8.25, 1, 1), (',', 9.25, 1, 1), ('.', 10.25, 1, 1),
    ('/', 11.25, 1, 1), ('Shift', 12.25, 1, 2.75),  # 改为 Shift

    # Row 5
    ('Ctrl', 0, 0, 1.25), ('Win', 1.25, 0, 1.25), ('Alt', 2.5, 0, 1.25),
    ('Space', 3.75, 0, 6.25),
    ('Alt', 10, 0, 1.25), ('Fn', 11.25, 0, 1.25), ('Ctrl', 12.5, 0, 1.25), ('<', 13.75, 0, 1.25)
]

COLOR_MAP = ['#161b22', '#5a3e02', '#9a6700', '#d29922', '#ffdf5d']


def draw_keyboard_heatmap(ax, key_data):
    ax.clear()
    ax.set_aspect('equal')
    ax.axis('off')

    max_val = max(key_data.values()) if key_data else 1
    cmap = mcolors.LinearSegmentedColormap.from_list("key_hot", COLOR_MAP, N=100)

    for key_label, x, y, w in KEYBOARD_LAYOUT:
        # 匹配键名
        lookup_key = key_label.upper()
        if key_label == 'Back': lookup_key = 'BACKSPACE'
        if key_label == 'Shift': lookup_key = 'SHIFT'
        if key_label == 'Ctrl': lookup_key = 'CTRL_L'
        if key_label == 'Alt': lookup_key = 'ALT_L'
        if key_label == 'Space': lookup_key = 'SPACE'
        if key_label == 'Win': lookup_key = 'CMD'  # 或 KEY.CMD

        count = key_data.get(lookup_key, 0)

        color_val = (count / max_val) if max_val > 0 else 0
        face_color = cmap(color_val) if count > 0 else '#161b22'
        edge_color = '#30363d'

        rect = patches.Rectangle((x, y), w, 1, linewidth=1, edgecolor=edge_color, facecolor=face_color)
        ax.add_patch(rect)

        font_size = 8 if len(key_label) > 1 else 10
        text_color = 'black' if color_val > 0.6 else '#c9d1d9'
        ax.text(x + w / 2, y + 0.5, key_label, ha='center', va='center', fontsize=font_size, color=text_color)

    ax.set_xlim(-0.5, 15.5)
    ax.set_ylim(-0.5, 5.5)