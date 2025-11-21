# 文件路径: database/__init__.py

from .service import DatabaseManager

# 创建一个单例实例供外部使用
db = DatabaseManager()

# 定义包的导出列表
__all__ = ['db', 'DatabaseManager']