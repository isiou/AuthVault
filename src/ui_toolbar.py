"""
GUI工具栏组件
负责顶部工具栏的创建和管理
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ToolbarComponent:
    """工具栏组件类"""

    def __init__(self, parent_frame: ttk.Frame):
        self.parent = parent_frame
        self.toolbar = None
        self.search_var = None

        # 回调函数
        self.on_search_callback: Optional[Callable[[str], None]] = None
        self.on_add_callback: Optional[Callable[[], None]] = None
        self.on_edit_callback: Optional[Callable[[], None]] = None
        self.on_delete_callback: Optional[Callable[[], None]] = None
        self.on_backup_callback: Optional[Callable[[], None]] = None
        self.on_restore_callback: Optional[Callable[[], None]] = None
        self.on_scan_qr_callback: Optional[Callable[[], None]] = None
        self.on_screenshot_callback: Optional[Callable[[], None]] = None

    def create(self) -> ttk.Frame:
        """创建工具栏"""
        self.toolbar = ttk.Frame(self.parent)
        self.toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # 创建搜索区域
        self._create_search_area()

        # 创建按钮区域
        self._create_button_area()

        return self.toolbar

    def _create_search_area(self):
        """创建搜索区域"""
        search_frame = ttk.Frame(self.toolbar)
        search_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(search_frame, text="搜索: ").pack(side=tk.LEFT, padx=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT)

    def _create_button_area(self):
        """创建按钮区域"""
        button_frame = ttk.Frame(self.toolbar)
        button_frame.pack(side=tk.RIGHT)

        # 定义按钮配置
        buttons = [
            ("添\u3000\u3000加", self._on_add_clicked),
            ("编\u3000\u3000辑", self._on_edit_clicked),
            ("删\u3000\u3000除", self._on_delete_clicked),
            ("备\u3000\u3000份", self._on_backup_clicked),
            ("导\u3000\u3000入", self._on_restore_clicked),
            ("扫码添加", self._on_scan_qr_clicked),
            ("截图添加", self._on_screenshot_clicked),
        ]

        for text, command in buttons:
            ttk.Button(button_frame, text=text, command=command, width=12).pack(
                side=tk.LEFT, padx=1
            )

    def _on_search_change(self, *args):
        """搜索内容变化事件"""
        if self.on_search_callback:
            search_text = self.search_var.get()
            self.on_search_callback(search_text)

    def _on_add_clicked(self):
        """添加按钮点击事件"""
        if self.on_add_callback:
            self.on_add_callback()

    def _on_edit_clicked(self):
        """编辑按钮点击事件"""
        if self.on_edit_callback:
            self.on_edit_callback()

    def _on_delete_clicked(self):
        """删除按钮点击事件"""
        if self.on_delete_callback:
            self.on_delete_callback()

    def _on_backup_clicked(self):
        """备份按钮点击事件"""
        if self.on_backup_callback:
            self.on_backup_callback()

    def _on_restore_clicked(self):
        """导入按钮点击事件"""
        if self.on_restore_callback:
            self.on_restore_callback()

    def _on_scan_qr_clicked(self):
        """扫码添加按钮点击事件"""
        if self.on_scan_qr_callback:
            self.on_scan_qr_callback()

    def _on_screenshot_clicked(self):
        """截图添加按钮点击事件"""
        if self.on_screenshot_callback:
            self.on_screenshot_callback()

    def set_search_callback(self, callback: Callable[[str], None]):
        """设置搜索回调函数"""
        self.on_search_callback = callback

    def set_add_callback(self, callback: Callable[[], None]):
        """设置添加按钮回调函数"""
        self.on_add_callback = callback

    def set_edit_callback(self, callback: Callable[[], None]):
        """设置编辑按钮回调函数"""
        self.on_edit_callback = callback

    def set_delete_callback(self, callback: Callable[[], None]):
        """设置删除按钮回调函数"""
        self.on_delete_callback = callback

    def set_backup_callback(self, callback: Callable[[], None]):
        """设置备份按钮回调函数"""
        self.on_backup_callback = callback

    def set_restore_callback(self, callback: Callable[[], None]):
        """设置导入按钮回调函数"""
        self.on_restore_callback = callback

    def set_scan_qr_callback(self, callback: Callable[[], None]):
        """设置扫码添加按钮回调函数"""
        self.on_scan_qr_callback = callback

    def set_screenshot_callback(self, callback: Callable[[], None]):
        """设置截图添加按钮回调函数"""
        self.on_screenshot_callback = callback

    def get_search_text(self) -> str:
        """获取当前搜索文本"""
        return self.search_var.get() if self.search_var else ""

    def clear_search(self):
        """清空搜索框"""
        if self.search_var:
            self.search_var.set("")
