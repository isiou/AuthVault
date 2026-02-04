"""
工具栏组件
提供应用程序的主要操作按钮和搜索功能
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

try:
    from src.core.config_manager import ConfigManager
except ImportError:
    from core.config_manager import ConfigManager


class ToolbarComponent:
    """工具栏组件"""

    def __init__(self, parent, config_manager: Optional[ConfigManager] = None):
        self.parent = parent
        self.config_manager = config_manager

        # 回调函数
        self.search_callback: Optional[Callable[[str], None]] = None
        self.add_callback: Optional[Callable[[], None]] = None
        self.edit_callback: Optional[Callable[[], None]] = None
        self.delete_callback: Optional[Callable[[], None]] = None
        self.backup_callback: Optional[Callable[[], None]] = None
        self.restore_callback: Optional[Callable[[], None]] = None
        self.scan_qr_callback: Optional[Callable[[], None]] = None
        self.screenshot_callback: Optional[Callable[[], None]] = None

        # UI变量
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)

    def create(self) -> ttk.Frame:
        """创建工具栏"""
        # 工具栏框架
        toolbar_frame = ttk.Frame(self.parent)
        toolbar_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        toolbar_frame.columnconfigure(1, weight=1)

        # 左侧按钮组
        left_frame = ttk.Frame(toolbar_frame)
        left_frame.grid(row=0, column=0, sticky=tk.W)

        # 添加按钮
        add_btn = ttk.Button(left_frame, text="添加", command=self._on_add)
        add_btn.grid(row=0, column=0, padx=(0, 5))

        # 编辑按钮
        edit_btn = ttk.Button(left_frame, text="编辑", command=self._on_edit)
        edit_btn.grid(row=0, column=1, padx=(0, 5))

        # 删除按钮
        delete_btn = ttk.Button(left_frame, text="删除", command=self._on_delete)
        delete_btn.grid(row=0, column=2, padx=(0, 20))

        # 扫描二维码按钮
        scan_btn = ttk.Button(left_frame, text="扫描二维码", command=self._on_scan_qr)
        scan_btn.grid(row=0, column=3, padx=(0, 5))

        # 截图识别按钮
        screenshot_btn = ttk.Button(
            left_frame, text="截图识别", command=self._on_screenshot
        )
        screenshot_btn.grid(row=0, column=4, padx=(0, 20))

        # 备份按钮
        backup_btn = ttk.Button(left_frame, text="备份", command=self._on_backup)
        backup_btn.grid(row=0, column=5, padx=(0, 5))

        # 恢复按钮
        restore_btn = ttk.Button(left_frame, text="恢复", command=self._on_restore)
        restore_btn.grid(row=0, column=6, padx=(0, 5))

        # 右侧搜索框
        search_frame = ttk.Frame(toolbar_frame)
        search_frame.grid(row=0, column=2, sticky=tk.E)

        ttk.Label(search_frame, text="搜索:").grid(row=0, column=0, padx=(0, 5))

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.grid(row=0, column=1)

        return toolbar_frame

    def _on_search_change(self, *args):
        """搜索内容变化"""
        if self.search_callback:
            self.search_callback(self.search_var.get())

    def _on_add(self):
        """添加按钮点击"""
        if self.add_callback:
            self.add_callback()

    def _on_edit(self):
        """编辑按钮点击"""
        if self.edit_callback:
            self.edit_callback()

    def _on_delete(self):
        """删除按钮点击"""
        if self.delete_callback:
            self.delete_callback()

    def _on_backup(self):
        """备份按钮点击"""
        if self.backup_callback:
            self.backup_callback()

    def _on_restore(self):
        """恢复按钮点击"""
        if self.restore_callback:
            self.restore_callback()

    def _on_scan_qr(self):
        """扫描二维码按钮点击"""
        if self.scan_qr_callback:
            self.scan_qr_callback()

    def _on_screenshot(self):
        """截图按钮点击"""
        if self.screenshot_callback:
            self.screenshot_callback()

    # 设置回调函数的方法
    def set_search_callback(self, callback: Callable[[str], None]):
        self.search_callback = callback

    def set_add_callback(self, callback: Callable[[], None]):
        self.add_callback = callback

    def set_edit_callback(self, callback: Callable[[], None]):
        self.edit_callback = callback

    def set_delete_callback(self, callback: Callable[[], None]):
        self.delete_callback = callback

    def set_backup_callback(self, callback: Callable[[], None]):
        self.backup_callback = callback

    def set_restore_callback(self, callback: Callable[[], None]):
        self.restore_callback = callback

    def set_scan_qr_callback(self, callback: Callable[[], None]):
        self.scan_qr_callback = callback

    def set_screenshot_callback(self, callback: Callable[[], None]):
        self.screenshot_callback = callback
