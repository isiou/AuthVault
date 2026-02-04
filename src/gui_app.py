import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import pyotp
import time
from datetime import datetime
import threading
import ctypes
from typing import Optional, Dict, Any
import sys
import os

# 添加父目录到Python路径，以便能够导入src模块
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

from src.storage_manager import StorageManager
from src.qr_service import get_qr_service
from src.screenshot_tool import capture_and_decode
from src.ui_toolbar import ToolbarComponent
from src.ui_account_list import AccountListComponent
from src.ui_code_display import CodeDisplayComponent
from src.exceptions import (
    StorageException,
    AccountException,
    QRCodeException,
    AccountNotFoundError,
    AccountAlreadyExistsError,
    ValidationException,
)

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class TwoFactorAuthGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("2FA 管理器")
        # 设置窗口大小和最小尺寸
        self.root.geometry("1330x800")
        self.root.minsize(1330, 800)

        # 配置 Treeview 样式
        style = ttk.Style()
        # 配置字体
        style.configure("Treeview", rowheight=36, font=("Microsoft YaHei UI", 10))
        style.configure(
            "Treeview.Heading",
            font=("Microsoft YaHei UI", 10),
        )

        # 初始化存储管理器
        self.storage = StorageManager()

        # 初始化二维码服务
        self.qr_service = get_qr_service()

        # 当前选中的账号
        self.selected_account: Optional[Dict[str, Any]] = None

        # 更新线程控制
        self.update_running = False
        self.update_thread = None

        # UI组件
        self.toolbar: Optional[ToolbarComponent] = None
        self.account_list: Optional[AccountListComponent] = None
        self.code_display: Optional[CodeDisplayComponent] = None
        self.status_label = None
        self.time_status_label = None

        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 创建 UI
        self.create_ui()

        # 加载账号数据
        self.load_accounts()

        # 启动自动更新
        self.start_auto_update()

    def create_ui(self):
        """创建用户界面"""
        # 主容器
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)

        # 创建工具栏组件
        self.toolbar = ToolbarComponent(main_container)
        toolbar_frame = self.toolbar.create()
        self._setup_toolbar_callbacks()

        # 中间主要内容区域
        content_frame = ttk.Frame(main_container)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        # 创建账号列表组件
        self.account_list = AccountListComponent(content_frame)
        account_list_frame = self.account_list.create()
        self._setup_account_list_callbacks()

        # 创建验证码显示组件
        self.code_display = CodeDisplayComponent(content_frame)
        code_display_frame = self.code_display.create()
        self._setup_code_display_callbacks()

        # 底部状态栏
        self.create_status_bar(main_container)

    def _setup_toolbar_callbacks(self):
        """设置工具栏回调函数"""
        self.toolbar.set_search_callback(self.on_search)
        self.toolbar.set_add_callback(self.add_account)
        self.toolbar.set_edit_callback(self.edit_account)
        self.toolbar.set_delete_callback(self.delete_account)
        self.toolbar.set_backup_callback(self.backup_data)
        self.toolbar.set_restore_callback(self.restore_data)
        self.toolbar.set_scan_qr_callback(self.scan_qr_add)
        self.toolbar.set_screenshot_callback(self.screenshot_add)

    def _setup_account_list_callbacks(self):
        """设置账号列表回调函数"""
        self.account_list.set_select_callback(self.on_account_select)
        self.account_list.set_double_click_callback(self.edit_account)

    def _setup_code_display_callbacks(self):
        """设置验证码显示回调函数"""
        self.code_display.set_copy_callback(self.copy_code)

    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent, relief=tk.SUNKEN, borderwidth=1)
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(status_frame, text="就绪", anchor=tk.W)
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=2)

        self.time_status_label = ttk.Label(
            status_frame, text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), anchor=tk.E
        )
        self.time_status_label.grid(row=0, column=1, sticky=tk.E, padx=5, pady=2)

    def load_accounts(self):
        """加载账号列表"""
        accounts = self.storage.get_all_accounts()
        if self.account_list:
            self.account_list.load_accounts(accounts)
        self.update_status(f"已加载 {len(accounts)} 个账号")

    def on_search(self, search_text: str):
        """搜索账号"""
        accounts = self.storage.get_all_accounts()
        if self.account_list:
            self.account_list.filter_accounts(accounts, search_text)

    def on_account_select(self, account_id: Optional[str]):
        """账号选择事件"""
        if account_id:
            account = self.storage.get_account(account_id)
            if account:
                self.selected_account = account
                if self.code_display:
                    self.code_display.update_account(account)
            else:
                self.selected_account = None
                if self.code_display:
                    self.code_display.clear_display()
        else:
            self.selected_account = None
            if self.code_display:
                self.code_display.clear_display()

    def copy_code(self, code: str):
        """复制验证码到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.update_status("验证码已复制到剪贴板")

    def add_account(self):
        """添加账号"""
        dialog = AccountDialog(self.root, "添加账号")
        if dialog.result:
            account_data = dialog.result
            try:
                account_id = self.storage.add_account(
                    account_data["name"], account_data["secret"], account_data["note"]
                )
                self.load_accounts()
                self.update_status("账号添加成功")

                # 选中新添加的账号
                if self.account_list:
                    self.account_list.select_account(account_id)

            except AccountAlreadyExistsError as e:
                messagebox.showerror("错误", str(e))
            except (StorageException, AccountException) as e:
                messagebox.showerror("错误", str(e))

    def edit_account(self):
        """编辑账号"""
        if not self.selected_account:
            messagebox.showwarning("提示", "请先选择要编辑的账号")
            return

        dialog = AccountDialog(self.root, "编辑账号", self.selected_account)
        if dialog.result:
            account_data = dialog.result
            try:
                self.storage.update_account(
                    self.selected_account["id"],
                    account_data["name"],
                    account_data["secret"],
                    account_data["note"],
                )
                self.load_accounts()

                # 更新当前选中的账号
                updated_account = self.storage.get_account(self.selected_account["id"])
                if updated_account:
                    self.selected_account = updated_account
                    if self.code_display:
                        self.code_display.update_account(updated_account)
                    if self.account_list:
                        self.account_list.select_account(updated_account["id"])

                self.update_status("账号更新成功")

            except (AccountNotFoundError, AccountAlreadyExistsError) as e:
                messagebox.showerror("错误", str(e))
            except (StorageException, AccountException) as e:
                messagebox.showerror("错误", str(e))

    def delete_account(self):
        """删除账号"""
        if not self.selected_account:
            messagebox.showwarning("提示", "请先选择要删除的账号")
            return

        if messagebox.askyesno(
            "确认删除", f"确定要删除账号 '{self.selected_account['name']}' 吗？"
        ):
            try:
                self.storage.delete_account(self.selected_account["id"])
                self.selected_account = None
                self.load_accounts()
                if self.code_display:
                    self.code_display.clear_display()
                if self.account_list:
                    self.account_list.clear_selection()
                self.update_status("账号删除成功")
            except AccountNotFoundError as e:
                messagebox.showerror("错误", str(e))
            except (StorageException, AccountException) as e:
                messagebox.showerror("错误", str(e))

    def backup_data(self):
        """备份数据"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".2fa",
            filetypes=[("2FA 备份文件", "*.2fa"), ("所有文件", "*.*")],
            initialfile=f"2fa_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.2fa",
        )

        if filename:
            success, message = self.storage.backup(filename)
            if success:
                messagebox.showinfo("成功", "数据备份成功！")
                self.update_status(f"备份已保存: {filename}")
            else:
                messagebox.showerror("错误", f"备份失败: {message}")

    def restore_data(self):
        """恢复数据"""
        filename = filedialog.askopenfilename(
            filetypes=[("2FA 备份文件", "*.2fa"), ("所有文件", "*.*")]
        )

        if filename:
            if messagebox.askyesno(
                "确认恢复", "恢复数据将覆盖当前所有账号，确定继续吗？"
            ):
                success, message = self.storage.restore(filename)
                if success:
                    self.selected_account = None
                    self.load_accounts()
                    if self.code_display:
                        self.code_display.clear_display()
                    if self.account_list:
                        self.account_list.clear_selection()
                    messagebox.showinfo("成功", "数据恢复成功！")
                    self.update_status(f"从备份恢复: {filename}")
                else:
                    messagebox.showerror("错误", f"恢复失败: {message}")

    def scan_qr_add(self):
        """扫描二维码添加账号"""
        filename = filedialog.askopenfilename(
            title="选择二维码图片",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("PNG 文件", "*.png"),
                ("JPEG 文件", "*.jpg *.jpeg"),
                ("所有文件", "*.*"),
            ],
        )

        if not filename:
            return

        try:
            # 使用新的二维码服务解析
            info = self.qr_service.extract_2fa_from_file(filename)

            # 显示解析结果并确认添加
            result_msg = (
                f"解析成功！\n\n"
                f"发行者: {info['issuer']}\n"
                f"账号: {info['account']}\n"
                f"密钥: {info['secret']}\n\n"
                f"是否添加此账号？"
            )

            if messagebox.askyesno("确认添加", result_msg):
                # 生成账号名称
                if info["issuer"]:
                    name = f"{info['issuer']} ({info['account']})"
                else:
                    name = info["account"]

                try:
                    # 添加账号
                    account_id = self.storage.add_account(
                        name, info["secret"], f"从二维码导入 - {info['account']}"
                    )
                    self.load_accounts()

                    # 选中新添加的账号
                    if self.account_list:
                        self.account_list.select_account(account_id)

                    self.update_status(f"账号 '{name}' 添加成功")
                    messagebox.showinfo("成功", f"账号 '{name}' 已添加！")

                except AccountAlreadyExistsError as e:
                    messagebox.showerror("错误", str(e))
                except (StorageException, AccountException) as e:
                    messagebox.showerror("错误", str(e))

        except QRCodeException as e:
            messagebox.showerror("错误", f"二维码解析失败:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")

    def screenshot_add(self):
        """截图识别二维码添加账号"""

        def on_result(info, error):
            """截图识别回调"""
            if error:
                messagebox.showerror("错误", f"识别失败:\n{error}")
                return

            # 显示解析结果并确认添加
            result_msg = (
                f"识别成功！\n\n"
                f"发行者: {info['issuer']}\n"
                f"账\u3000号: {info['account']}\n"
                f"密\u3000钥: {info['secret']}\n\n"
                f"是否添加此账号？"
            )

            if messagebox.askyesno("确认添加", result_msg):
                # 生成账号名称
                if info["issuer"]:
                    name = f"{info['issuer']} ({info['account']})"
                else:
                    name = info["account"]

                try:
                    # 添加账号
                    account_id = self.storage.add_account(
                        name, info["secret"], f"从截图导入 - {info['account']}"
                    )
                    self.load_accounts()

                    # 选中新添加的账号
                    if self.account_list:
                        self.account_list.select_account(account_id)

                    self.update_status(f"账号 '{name}' 添加成功")
                    messagebox.showinfo("成功", f"账号 '{name}' 已添加！")

                except AccountAlreadyExistsError as e:
                    messagebox.showerror("错误", str(e))
                except (StorageException, AccountException) as e:
                    messagebox.showerror("错误", str(e))

        # 启动截图工具
        capture_and_decode(self.root, on_result)

    def start_auto_update(self):
        """启动自动更新线程"""
        self.update_running = True
        self.update_thread = threading.Thread(target=self.auto_update_loop, daemon=True)
        self.update_thread.start()

    def auto_update_loop(self):
        """自动更新循环"""
        while self.update_running:
            try:
                # 更新验证码显示
                if self.selected_account and self.code_display:
                    self.root.after(0, self.code_display.refresh_code)

                # 更新状态栏时间
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if self.time_status_label:
                    self.root.after(
                        0, lambda: self.time_status_label.config(text=current_time)
                    )

            except Exception as e:
                print(f"更新错误: {e}")

            time.sleep(1)

    def update_status(self, message):
        """更新状态栏"""
        self.status_label.config(text=message)

    def on_closing(self):
        """窗口关闭事件"""
        self.update_running = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
        self.root.destroy()


class AccountDialog(simpledialog.Dialog):
    """账号添加/编辑对话框"""

    def __init__(self, parent, title, account=None):
        self.account = account
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        """创建对话框内容"""
        ttk.Label(master, text="账号名称: ").grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.name_entry = ttk.Entry(master, width=40)
        self.name_entry.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(master, text="密\u3000\u3000钥:").grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.secret_entry = ttk.Entry(master, width=40)
        self.secret_entry.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(master, text="备\u3000\u3000注:").grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=5
        )
        self.note_entry = ttk.Entry(master, width=40)
        self.note_entry.grid(row=2, column=1, pady=5, padx=5)

        if self.account:
            self.name_entry.insert(0, self.account["name"])
            self.secret_entry.insert(0, self.account["secret"])
            self.note_entry.insert(0, self.account["note"])

        return self.name_entry

    def validate(self):
        """验证输入"""
        name = self.name_entry.get().strip()
        secret = self.secret_entry.get().strip().upper().replace(" ", "")

        if not name:
            messagebox.showwarning("提示", "请输入账号名称")
            return False

        if not secret:
            messagebox.showwarning("提示", "请输入密钥")
            return False

        # 验证密钥格式
        try:
            pyotp.TOTP(secret).now()
        except Exception:
            messagebox.showwarning("提示", "密钥格式无效，请检查TOTP密钥是否正确")
            return False

        return True

    def apply(self):
        """应用结果"""
        self.result = {
            "name": self.name_entry.get().strip(),
            "secret": self.secret_entry.get().strip().upper().replace(" ", ""),
            "note": self.note_entry.get().strip(),
        }


def main():
    """主函数"""
    root = tk.Tk()

    try:
        root.iconbitmap("icon.ico")
    except:
        pass

    app = TwoFactorAuthGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
