"""
账号添加/编辑对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pyotp
from typing import Dict, Any, Optional

try:
    from src.core.totp_service import TOTPService
    from src.utils.exceptions import TOTPException
except ImportError:
    from core.totp_service import TOTPService
    from utils.exceptions import TOTPException


class AccountDialog(simpledialog.Dialog):
    """账号添加/编辑对话框"""

    def __init__(self, parent, title, account: Optional[Dict[str, Any]] = None):
        """初始化对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            account: 要编辑的账号信息，为None时为添加模式
        """
        self.account = account
        self.result = None
        self.totp_service = TOTPService()
        super().__init__(parent, title)

    def body(self, master):
        """创建对话框内容"""
        # 设置对话框大小
        self.geometry("400x200")
        self.resizable(False, False)

        # 账号名称
        ttk.Label(master, text="账号名称:").grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.name_entry = ttk.Entry(master, width=40)
        self.name_entry.grid(row=0, column=1, pady=5, padx=5, sticky=(tk.W, tk.E))

        # TOTP密钥
        ttk.Label(master, text="TOTP密钥:").grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.secret_entry = ttk.Entry(master, width=40, show="*")
        self.secret_entry.grid(row=1, column=1, pady=5, padx=5, sticky=(tk.W, tk.E))

        # 显示/隐藏密钥按钮
        self.show_secret_var = tk.BooleanVar()
        self.show_secret_check = ttk.Checkbutton(
            master,
            text="显示密钥",
            variable=self.show_secret_var,
            command=self.toggle_secret_visibility,
        )
        self.show_secret_check.grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)

        # 备注
        ttk.Label(master, text="备注:").grid(
            row=3, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.note_entry = ttk.Entry(master, width=40)
        self.note_entry.grid(row=3, column=1, pady=5, padx=5, sticky=(tk.W, tk.E))

        # 测试按钮
        self.test_button = ttk.Button(master, text="测试密钥", command=self.test_secret)
        self.test_button.grid(row=4, column=1, sticky=tk.E, pady=5, padx=5)

        # 配置列权重
        master.columnconfigure(1, weight=1)

        # 如果是编辑模式，填入现有数据
        if self.account:
            self.name_entry.insert(0, self.account.get("name", ""))
            self.secret_entry.insert(0, self.account.get("secret", ""))
            self.note_entry.insert(0, self.account.get("note", ""))

        return self.name_entry  # 返回初始焦点控件

    def toggle_secret_visibility(self):
        """切换密钥显示/隐藏"""
        if self.show_secret_var.get():
            self.secret_entry.config(show="")
        else:
            self.secret_entry.config(show="*")

    def test_secret(self):
        """测试TOTP密钥"""
        secret = self.secret_entry.get().strip()
        if not secret:
            messagebox.showwarning("提示", "请先输入TOTP密钥")
            return

        try:
            # 使用TOTP服务测试密钥
            totp_info = self.totp_service.generate_totp(secret)
            code = totp_info["code"]
            remaining_time = totp_info["remaining_time"]

            messagebox.showinfo(
                "测试成功",
                f"TOTP密钥有效！\n\n"
                f"当前验证码: {code}\n"
                f"剩余时间: {remaining_time}秒",
            )
        except TOTPException as e:
            messagebox.showerror("测试失败", f"密钥无效:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("测试失败", f"发生错误: {str(e)}")

    def validate(self):
        """验证输入"""
        name = self.name_entry.get().strip()
        secret = self.secret_entry.get().strip()

        # 验证账号名称
        if not name:
            messagebox.showwarning("提示", "请输入账号名称")
            return False

        if len(name) > 100:
            messagebox.showwarning("提示", "账号名称过长（最多100个字符）")
            return False

        # 验证密钥
        if not secret:
            messagebox.showwarning("提示", "请输入TOTP密钥")
            return False

        # 验证密钥格式
        try:
            self.totp_service.normalize_secret(secret)
        except TOTPException:
            messagebox.showwarning("提示", "密钥格式无效，请检查TOTP密钥是否正确")
            return False

        return True

    def apply(self):
        """应用结果"""
        name = self.name_entry.get().strip()
        secret = self.secret_entry.get().strip()
        note = self.note_entry.get().strip()

        # 标准化密钥
        try:
            normalized_secret = self.totp_service.normalize_secret(secret)
        except TOTPException:
            normalized_secret = secret

        self.result = {
            "name": name,
            "secret": normalized_secret,
            "note": note,
        }

    def buttonbox(self):
        """创建按钮框"""
        # 创建按钮框架
        box = ttk.Frame(self)

        # 确定按钮
        ok_button = ttk.Button(
            box, text="确定", width=10, command=self.ok, default=tk.ACTIVE
        )
        ok_button.pack(side=tk.LEFT, padx=(0, 5))

        # 取消按钮
        cancel_button = ttk.Button(box, text="取消", width=10, command=self.cancel)
        cancel_button.pack(side=tk.LEFT)

        # 绑定键盘事件
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack(pady=10)
