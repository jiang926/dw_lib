import sys
import os

# 获取当前文件所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 获取项目根目录（factor_cli 的父目录）
project_root = os.path.dirname(current_dir)

# 确保根目录在 sys.path 中
if project_root not in sys.path:
    sys.path.append(project_root)
