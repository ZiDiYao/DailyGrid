from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property


class AnimatedLabel(QLabel):
    """
    一个自带数字滚动动画的 Label
    """

    def __init__(self, value=0, parent=None):
        # 初始显示
        text = str(value)
        super().__init__(text, parent)

        # 确保初始值是整数
        if isinstance(value, (int, float)):
            self._current_value = int(value)
        else:
            self._current_value = 0

        self.is_time_format = False
        self._target_value = self._current_value  # 记录目标值，防止重复动画

    def get_value(self):
        return self._current_value

    def set_value(self, val):
        # Property 的 setter，每一帧动画都会调用这里
        self._current_value = val

        # 根据格式刷新显示文本
        if self.is_time_format:
            h = int(val // 3600)
            m = int((val % 3600) // 60)
            self.setText(f"{h}h {m}m")
        else:
            self.setText(str(int(val)))

    # 注册属性，让 QPropertyAnimation 可以修改它
    animated_value = Property(int, get_value, set_value)

    def transition_to(self, new_value, is_time=False):
        """
        从当前值平滑过渡到新值
        """
        self.is_time_format = is_time
        target = int(new_value)

        # 【关键修复】只有当数值真的改变了，才启动动画
        if target == self._target_value:
            # 如果是时间格式，虽然数值没变，但可能需要强制刷新一下格式（保险起见）
            if is_time:
                self.set_value(target)
            return

        self._target_value = target

        # 创建并启动动画
        self.anim = QPropertyAnimation(self, b"animated_value")
        self.anim.setDuration(600)  # 动画时长 600ms
        self.anim.setStartValue(self._current_value)
        self.anim.setEndValue(target)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)  # 缓动曲线
        self.anim.start()


class StatCard(QFrame):
    clicked = Signal()

    def __init__(self, title, value=0, theme_color="#1f6feb", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setCursor(Qt.PointingHandCursor)

        self.theme_color = theme_color
        self.is_selected = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("StatTitle")
        layout.addWidget(self.lbl_title)

        # 使用自定义动画 Label
        self.lbl_value = AnimatedLabel(value)
        self.lbl_value.setObjectName("StatValue")
        layout.addWidget(self.lbl_value)

        self.refresh_style()

    def update_value(self, new_value, is_time=False):
        # 调用动画过渡
        self.lbl_value.transition_to(new_value, is_time)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if not self.is_selected:
            self.setStyleSheet(f"""
                QFrame#Card {{
                    background-color: #21262d;
                    border: 1px solid #8b949e;
                }}
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.refresh_style()
        super().leaveEvent(event)

    def set_selected(self, selected):
        self.is_selected = selected
        self.refresh_style()

    def refresh_style(self):
        if self.is_selected:
            self.setStyleSheet(f"""
                QFrame#Card {{
                    background-color: #1c2128;
                    border: 1px solid {self.theme_color};
                    border-bottom: 2px solid {self.theme_color};
                }}
                QLabel#StatTitle {{
                    color: {self.theme_color};
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame#Card {
                    background-color: #161b22;
                    border: 1px solid #30363d;
                }
                QLabel#StatTitle {
                    color: #8b949e;
                }
            """)