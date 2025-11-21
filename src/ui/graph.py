import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import datetime
import numpy as np

# GitHub 官方深色模式色阶 (2025标准)
# 格式: [Level0(空), Level1, Level2, Level3, Level4]
GITHUB_PALETTE = {
    'bg': '#0d1117',  # 整个画布的背景色 (用于绘制格子的间隙)
    'empty': '#161b22',  # 空格子的颜色

    'screen_time_seconds': ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353'],  # 经典绿
    'mouse_clicks': ['#161b22', '#0c2d6b', '#005cc5', '#3192aa', '#79c0ff'],  # 科技蓝
    'keystrokes': ['#161b22', '#4d2d00', '#9a6700', '#d29922', '#ffdf5d']  # 活力橙 (稍微调亮了Level1)
}


class GithubHeatmap:
    def __init__(self, data_rows, metric='screen_time_seconds', year=None):
        self.data_rows = data_rows
        self.metric = metric
        self.year = year if year else datetime.date.today().year
        self.coord_map = {}

    def _prepare_data(self):
        data_map = {}
        metric_idx = 1
        if self.metric == 'mouse_clicks':
            metric_idx = 2
        elif self.metric == 'keystrokes':
            metric_idx = 3

        for row in self.data_rows:
            data_map[row[0]] = row[metric_idx]

        # 初始化矩阵 (7行 x 53列)
        self.heatmap_data = np.zeros((7, 53))
        self.month_labels = [""] * 53
        last_month = -1

        start_date = datetime.date(self.year, 1, 1)
        end_date = datetime.date(self.year, 12, 31)
        delta = datetime.timedelta(days=1)
        curr_date = start_date

        while curr_date <= end_date:
            date_str = str(curr_date)
            val = data_map.get(date_str, 0)

            display_val = val
            if self.metric == 'screen_time_seconds':
                display_val = val / 3600.0

            day_of_year = (curr_date - datetime.date(self.year, 1, 1)).days
            first_day_weekday = start_date.weekday()

            col = (day_of_year + first_day_weekday) // 7
            row = curr_date.weekday()

            if col < 53:
                self.heatmap_data[row, col] = display_val
                self.coord_map[(row, col)] = (date_str, val, display_val)

                if row == 0:
                    if curr_date.month != last_month:
                        self.month_labels[col] = curr_date.strftime("%b")
                        last_month = curr_date.month

            curr_date += delta

    def plot(self, ax):
        self._prepare_data()
        ax.clear()

        # 1. 获取颜色列表
        colors = GITHUB_PALETTE.get(self.metric, GITHUB_PALETTE['screen_time_seconds'])

        # 2. 定义分级阈值 (BoundaryNorm)
        # 任何大于0的数据，都会立刻跳出深色背景，变成 Level 1
        vmax = 1
        if self.metric == 'screen_time_seconds':
            vmax = 8.0
        elif self.metric == 'mouse_clicks':
            vmax = 5000
        elif self.metric == 'keystrokes':
            vmax = 10000

        # 阈值设定: [0, 0.1, 25%, 50%, 75%, 100%]
        # 这样只要有数据 (>0)，颜色索引就是 1，而不是 0
        bounds = [0, 0.001, vmax * 0.25, vmax * 0.5, vmax * 0.75, vmax * 999]

        # 创建离散色图
        cmap = mcolors.ListedColormap(colors)
        norm = mcolors.BoundaryNorm(bounds, cmap.N)

        # 3. 绘图 (关键修复：edgecolors 设置为背景色，形成间隙)
        ax.pcolormesh(
            self.heatmap_data,
            cmap=cmap,
            norm=norm,
            edgecolors=GITHUB_PALETTE['bg'],  # 关键！用背景色切割格子
            linewidth=2,  # 增加间隙宽度，让格子更明显
        )

        ax.invert_yaxis()
        ax.set_aspect('equal')

        # 4. 标签样式优化
        ax.set_yticks([0.5, 2.5, 4.5, 6.5])
        ax.set_yticklabels(['Mon', 'Wed', 'Fri', 'Sun'], fontsize=9, color='#8b949e')

        xticks = [i + 0.5 for i, label in enumerate(self.month_labels) if label != ""]
        xticklabels = [self.month_labels[int(i)] for i in xticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels, fontsize=9, color='#8b949e', ha='left')

        # 隐藏所有边框
        ax.tick_params(axis=u'both', which=u'both', length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)

    def get_info_by_coord(self, x, y):
        if x is None or y is None: return None
        col = int(x)
        row = int(y)
        return self.coord_map.get((row, col))