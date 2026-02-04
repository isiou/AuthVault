"""
验证码显示组件
显示选中账号的TOTP验证码和相关信息
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable, Optional
import threading

try:
    from src.core.config_manager import ConfigManager
    from src.core.totp_service import TOTPService
    from src.utils.exceptions import TOTPException
except ImportError:
    from core.config_manager import ConfigManager
    from core.totp_service import TOTPService
    from utils.exceptions import TOTPException


class CodeDisplayComponent:
    """验证码显示组件"""

    def __init__(
        self,
        parent,
        config_manager: Optional[ConfigManager] = None,
        totp_service: Optional[TOTPService] = None,
    ):
        self.parent = parent
        self.config_manager = config_manager
        self.totp_service = totp_service or TOTPService()

        # 当前账号信息
        self.current_account: Optional[Dict[str, Any]] = None

        # 回调函数
        self.copy_callback: Optional[Callable[[str], None]] = None

        # UI组件
        self.code_var = tk.StringVar(value="------")
        self.time_var = tk.StringVar(value="--")
        self.account_name_var = tk.StringVar(value="未选择账号")
        self.note_var = tk.StringVar(value="")

        # 进度条
        self.progress_var = tk.DoubleVar(value=0)

    def create(self) -> ttk.Frame:
        """创建验证码显示区域"""
        # 验证码显示框架
        code_frame = ttk.LabelFrame(self.parent, text="验证码", padding="10")
        code_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 账号名称
        name_label = ttk.Label(
            code_frame,
            textvariable=self.account_name_var,
            font=("Microsoft YaHei UI", 14, "bold"),
        )
        name_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # 验证码显示
        code_frame_inner = ttk.Frame(code_frame)
        code_frame_inner.grid(row=1, column=0, columnspan=2, pady=(0, 15))

        # 大号验证码
        code_label = ttk.Label(
            code_frame_inner,
            textvariable=self.code_var,
            font=("Consolas", 32, "bold"),
            foreground="blue",
        )
        code_label.grid(row=0, column=0, padx=(0, 10))

        # 复制按钮
        copy_btn = ttk.Button(code_frame_inner, text="复制", command=self._on_copy)
        copy_btn.grid(row=0, column=1)

        # 时间进度条
        progress_frame = ttk.Frame(code_frame)
        progress_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        progress_frame.columnconfigure(0, weight=1)

        # 进度条
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            style="TProgressbar",
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # 剩余时间
        time_label = ttk.Label(
            progress_frame, textvariable=self.time_var, font=("Microsoft YaHei UI", 10)
        )
        time_label.grid(row=0, column=1, padx=(10, 0))

        # 备注信息
        note_label = ttk.Label(
            code_frame,
            textvariable=self.note_var,
            font=("Microsoft YaHei UI", 9),
            foreground="gray",
        )
        note_label.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        # 配置权重
        code_frame.columnconfigure(0, weight=1)

        return code_frame

    def update_account(self, account: Dict[str, Any]):
        """更新显示的账号"""
        self.current_account = account
        self.account_name_var.set(account.get("name", "未知账号"))
        self.note_var.set(account.get("note", ""))
        self.refresh_code()

    def clear_display(self):
        """清空显示"""
        self.current_account = None
        self.account_name_var.set("未选择账号")
        self.note_var.set("")
        self.code_var.set("------")
        self.time_var.set("--")
        self.progress_var.set(0)

    def refresh_code(self):
        """刷新验证码"""
        if not self.current_account:
            return

        try:
            # 生成TOTP验证码
            totp_info = self.totp_service.generate_totp(
                self.current_account.get("secret", "")
            )

            # 更新显示
            code = totp_info["code"]
            remaining_time = totp_info["remaining_time"]
            total_time = totp_info["total_time"]

            # 格式化验证码（添加空格分隔）
            formatted_code = f"{code[:3]} {code[3:]}"
            self.code_var.set(formatted_code)

            # 更新时间和进度
            self.time_var.set(f"{remaining_time}s")
            progress = (remaining_time / total_time) * 100
            self.progress_var.set(progress)

            # 根据剩余时间调整进度条颜色
            if remaining_time <= 5:
                # 时间不足时显示红色
                style = ttk.Style()
                style.configure("TProgressbar", background="red")
            elif remaining_time <= 10:
                # 时间较少时显示橙色
                style = ttk.Style()
                style.configure("TProgressbar", background="orange")
            else:
                # 正常时间显示绿色
                style = ttk.Style()
                style.configure("TProgressbar", background="green")

        except TOTPException as e:
            self.code_var.set("ERROR")
            self.time_var.set("--")
            self.progress_var.set(0)
            print(f"TOTP生成失败: {e}")
        except Exception as e:
            self.code_var.set("ERROR")
            self.time_var.set("--")
            self.progress_var.set(0)
            print(f"刷新验证码失败: {e}")

    def _on_copy(self):
        """复制按钮点击"""
        if self.current_account and self.copy_callback:
            # 获取原始验证码（移除空格）
            code = self.code_var.get().replace(" ", "")
            if code != "------" and code != "ERROR":
                self.copy_callback(code)

    def set_copy_callback(self, callback: Callable[[str], None]):
        """设置复制回调"""
        self.copy_callback = callback
