#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AuthVault - 双重认证管理器
主程序入口
"""

import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 导入新的应用入口
from src.app import main

if __name__ == "__main__":
    main()
