"""
账号列表组件
显示和管理账号列表
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Callable, Optional

try:
    from src.core.config_manager import ConfigManager
except ImportError:
    from core.config_manager import ConfigManager


class AccountListComponent:
    """账号列表组件"""

    def __init__(self, parent, config_manager: Optional[ConfigManager] = None):
        self.parent = parent
        self.config_manager = config_manager

        # 数据
        self.accounts: List[Dict[str, Any]] = []

        # 回调函数
        self.select_callback: Optional[Callable[[Optional[str]], None]] = None
        self.double_click_callback: Optional[Callable[[], None]] = None

        # UI组件
        self.tree: Optional[ttk.Treeview] = None

    def create(self) -> ttk.Frame:
        """创建账号列表"""
        # 账号列表框架
        list_frame = ttk.LabelFrame(self.parent, text="账号列表", padding="5")
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # 创建 Treeview
        columns = ("name", "note", "created")
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=15
        )

        # 设置列标题
        self.tree.heading("name", text="账号名称")
        self.tree.heading("note", text="备注")
        self.tree.heading("created", text="创建时间")

        # 设置列宽
        self.tree.column("name", width=200)
        self.tree.column("note", width=150)
        self.tree.column("created", width=120)

        # 滚动条
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 布局
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 配置权重
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # 绑定事件
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)

        return list_frame

    def load_accounts(self, accounts: List[Dict[str, Any]]):
        """加载账号列表"""
        self.accounts = accounts

        # 清空现有数据
        if self.tree:
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 添加新数据
            for account in accounts:
                # 格式化创建时间
                created_at = account.get("created_at", "")
                if created_at:
                    try:
                        from datetime import datetime

                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        created_display = dt.strftime("%Y-%m-%d")
                    except:
                        created_display = (
                            created_at[:10] if len(created_at) >= 10 else created_at
                        )
                else:
                    created_display = ""

                # 插入数据
                self.tree.insert(
                    "",
                    tk.END,
                    iid=account["id"],
                    values=(
                        account.get("name", ""),
                        account.get("note", ""),
                        created_display,
                    ),
                )

    def _on_select(self, event):
        """选择事件"""
        if self.tree:
            selection = self.tree.selection()
            if selection:
                account_id = selection[0]
                if self.select_callback:
                    self.select_callback(account_id)
            else:
                if self.select_callback:
                    self.select_callback(None)

    def _on_double_click(self, event):
        """双击事件"""
        if self.double_click_callback:
            self.double_click_callback()

    def select_account(self, account_id: str):
        """选中指定账号"""
        if self.tree:
            self.tree.selection_set(account_id)
            self.tree.focus(account_id)

    def clear_selection(self):
        """清空选择"""
        if self.tree:
            self.tree.selection_remove(self.tree.selection())

    def set_select_callback(self, callback: Callable[[Optional[str]], None]):
        """设置选择回调"""
        self.select_callback = callback

    def set_double_click_callback(self, callback: Callable[[], None]):
        """设置双击回调"""
        self.double_click_callback = callback
