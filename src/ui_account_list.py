"""
GUI账号列表组件
负责账号列表的显示和管理
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional, Callable


class AccountListComponent:
    """账号列表组件类"""

    def __init__(self, parent_frame: ttk.Frame):
        self.parent = parent_frame
        self.list_frame = None
        self.tree = None

        # 回调函数
        self.on_select_callback: Optional[Callable[[Optional[str]], None]] = None
        self.on_double_click_callback: Optional[Callable[[], None]] = None

        # 当前选中的账号ID
        self.selected_account_id: Optional[str] = None

    def create(self) -> ttk.LabelFrame:
        """创建账号列表组件"""
        self.list_frame = ttk.LabelFrame(self.parent, text="账号列表", padding="5")
        self.list_frame.grid(
            row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5)
        )
        self.list_frame.columnconfigure(0, weight=1)
        self.list_frame.rowconfigure(0, weight=1)

        # 创建表格
        self._create_treeview()

        return self.list_frame

    def _create_treeview(self):
        """创建Treeview表格"""
        # 创建 Treeview
        columns = ("index", "name", "note")
        self.tree = ttk.Treeview(
            self.list_frame, columns=columns, show="headings", selectmode="browse"
        )

        # 定义列
        self.tree.heading("index", text="序号")
        self.tree.heading("name", text="账号名称")
        self.tree.heading("note", text="备注")

        # 设置列宽
        self.tree.column("index", width=70, minwidth=70, stretch=False, anchor="center")
        self.tree.column("name", width=250, minwidth=150, stretch=False)
        self.tree.column("note", width=300, minwidth=150, stretch=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(
            self.list_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 绑定事件
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)
        self.tree.bind("<Double-Button-1>", self._on_double_click)

    def _on_selection_change(self, event):
        """选择变化事件"""
        selection = self.tree.selection()
        if selection:
            self.selected_account_id = selection[0]
        else:
            self.selected_account_id = None

        if self.on_select_callback:
            self.on_select_callback(self.selected_account_id)

    def _on_double_click(self, event):
        """双击事件"""
        if self.on_double_click_callback:
            self.on_double_click_callback()

    def load_accounts(self, accounts: List[Dict[str, Any]]):
        """
        加载账号列表

        Args:
            accounts: 账号数据列表
        """
        # 清空现有列表
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 重置选中状态
        self.selected_account_id = None

        # 加载账号
        for idx, account in enumerate(accounts, 1):
            self.tree.insert(
                "",
                tk.END,
                iid=account["id"],
                values=(str(idx), account["name"], account["note"]),
            )

    def filter_accounts(self, accounts: List[Dict[str, Any]], search_text: str):
        """
        过滤和显示账号

        Args:
            accounts: 所有账号数据
            search_text: 搜索文本
        """
        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 重置选中状态
        self.selected_account_id = None

        search_text = search_text.lower()
        idx = 0

        for account in accounts:
            if (
                search_text in account["name"].lower()
                or search_text in account["note"].lower()
            ):
                idx += 1
                self.tree.insert(
                    "",
                    tk.END,
                    iid=account["id"],
                    values=(str(idx), account["name"], account["note"]),
                )

    def get_selected_account_id(self) -> Optional[str]:
        """获取当前选中的账号ID"""
        return self.selected_account_id

    def select_account(self, account_id: str):
        """
        选中指定账号

        Args:
            account_id: 要选中的账号ID
        """
        if account_id in [item for item in self.tree.get_children()]:
            self.tree.selection_set(account_id)
            self.tree.focus(account_id)
            self.selected_account_id = account_id

    def clear_selection(self):
        """清空选择"""
        self.tree.selection_remove(self.tree.selection())
        self.selected_account_id = None

    def set_select_callback(self, callback: Callable[[Optional[str]], None]):
        """设置选择回调函数"""
        self.on_select_callback = callback

    def set_double_click_callback(self, callback: Callable[[], None]):
        """设置双击回调函数"""
        self.on_double_click_callback = callback

    def get_account_count(self) -> int:
        """获取当前显示的账号数量"""
        return len(self.tree.get_children())
