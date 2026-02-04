"""
主窗口界面
负责整个应用程序的主界面显示和交互
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import ctypes
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any

# 添加路径处理
if __name__ == "__main__" or "src." not in __name__:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(os.path.dirname(current_dir))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

try:
    from src.core.account_service import AccountService
    from src.core.totp_service import TOTPService
    from src.core.config_manager import ConfigManager
    from src.storage.encrypted_storage import EncryptedStorage
    from src.ui.components.toolbar import ToolbarComponent
    from src.ui.components.account_list import AccountListComponent
    from src.ui.components.code_display import CodeDisplayComponent
    from src.ui.dialogs.account_dialog import AccountDialog
    from src.utils.qr_decoder import QRCodeDecoder
    from src.utils.screenshot import capture_and_decode
    from src.utils.exceptions import (
        StorageException,
        AccountException,
        QRCodeException,
        AccountNotFoundError,
        AccountAlreadyExistsError,
    )
except ImportError:
    from core.account_service import AccountService
    from core.totp_service import TOTPService
    from core.config_manager import ConfigManager
    from storage.encrypted_storage import EncryptedStorage
    from ui.components.toolbar import ToolbarComponent
    from ui.components.account_list import AccountListComponent
    from ui.components.code_display import CodeDisplayComponent
    from ui.dialogs.account_dialog import AccountDialog
    from utils.qr_decoder import QRCodeDecoder
    from utils.screenshot import capture_and_decode
    from utils.exceptions import (
        StorageException,
        AccountException,
        QRCodeException,
        AccountNotFoundError,
        AccountAlreadyExistsError,
    )

# 设置DPI感知
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


class MainWindow:
    """主窗口类"""

    def __init__(self, root):
        self.root = root
        self.root.title("AuthVault - 双重认证管理器")

        # 初始化服务层
        self._init_services()

        # 加载配置
        self._load_config()

        # 设置窗口
        self._setup_window()

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

        # 创建UI
        self.create_ui()

        # 加载账号数据
        self.load_accounts()

        # 启动自动更新
        self.start_auto_update()

    def _init_services(self):
        """初始化服务层"""
        # 存储服务
        self.storage = EncryptedStorage()

        # TOTP服务
        self.totp_service = TOTPService()

        # 账户服务
        self.account_service = AccountService(self.storage, self.totp_service)

        # 配置管理器
        self.config_manager = ConfigManager()

        # 二维码解码器
        self.qr_decoder = QRCodeDecoder()

    def _load_config(self):
        """加载配置"""
        try:
            self.config_manager.load_config()
        except Exception as e:
            print(f"加载配置失败: {e}")

    def _setup_window(self):
        """设置窗口"""
        # 获取配置的窗口大小
        ui_config = self.config_manager.get_ui_config()
        window_size = ui_config.get("window_size", {"width": 1330, "height": 800})
        window_pos = ui_config.get("window_position", {"x": None, "y": None})

        # 设置窗口大小和最小尺寸
        width = window_size.get("width", 1330)
        height = window_size.get("height", 800)

        if window_pos.get("x") and window_pos.get("y"):
            self.root.geometry(f"{width}x{height}+{window_pos['x']}+{window_pos['y']}")
        else:
            self.root.geometry(f"{width}x{height}")

        self.root.minsize(800, 600)

        # 配置样式
        self._setup_styles()

    def _setup_styles(self):
        """设置UI样式"""
        style = ttk.Style()

        # 配置字体
        font_size = self.config_manager.get("ui.font_size", 10)
        font_family = "Microsoft YaHei UI"

        style.configure("Treeview", rowheight=36, font=(font_family, font_size))
        style.configure("Treeview.Heading", font=(font_family, font_size))

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
        self.toolbar = ToolbarComponent(main_container, self.config_manager)
        toolbar_frame = self.toolbar.create()
        self._setup_toolbar_callbacks()

        # 中间主要内容区域
        content_frame = ttk.Frame(main_container)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        # 创建账号列表组件
        self.account_list = AccountListComponent(content_frame, self.config_manager)
        account_list_frame = self.account_list.create()
        self._setup_account_list_callbacks()

        # 创建验证码显示组件
        self.code_display = CodeDisplayComponent(
            content_frame, self.config_manager, self.totp_service
        )
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
        try:
            accounts = self.account_service.get_all_accounts()
            if self.account_list:
                self.account_list.load_accounts(accounts)
            self.update_status(f"已加载 {len(accounts)} 个账号")
        except Exception as e:
            self.update_status(f"加载账号失败: {str(e)}")

    def on_search(self, search_text: str):
        """搜索账号"""
        try:
            accounts = self.account_service.search_accounts(search_text)
            if self.account_list:
                self.account_list.load_accounts(accounts)
            self.update_status(f"找到 {len(accounts)} 个匹配的账号")
        except Exception as e:
            self.update_status(f"搜索失败: {str(e)}")

    def on_account_select(self, account_id: Optional[str]):
        """账号选择事件"""
        if account_id:
            try:
                account = self.account_service.get_account(account_id)
                if account:
                    self.selected_account = account
                    if self.code_display:
                        self.code_display.update_account(account)
                else:
                    self.selected_account = None
                    if self.code_display:
                        self.code_display.clear_display()
            except Exception as e:
                self.update_status(f"加载账号失败: {str(e)}")
                self.selected_account = None
                if self.code_display:
                    self.code_display.clear_display()
        else:
            self.selected_account = None
            if self.code_display:
                self.code_display.clear_display()

    def copy_code(self, code: str):
        """复制验证码到剪贴板"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.update_status("验证码已复制到剪贴板")

            # 根据配置设置剪贴板超时清除
            timeout = self.config_manager.get("security.clipboard_timeout", 30)
            if timeout > 0:
                self.root.after(timeout * 1000, self._clear_clipboard)
        except Exception as e:
            self.update_status(f"复制失败: {str(e)}")

    def _clear_clipboard(self):
        """清除剪贴板"""
        try:
            self.root.clipboard_clear()
        except Exception:
            pass

    def add_account(self):
        """添加账号"""
        dialog = AccountDialog(self.root, "添加账号")
        if dialog.result:
            account_data = dialog.result
            try:
                account_id = self.account_service.add_account(
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
                self.account_service.update_account(
                    self.selected_account["id"],
                    account_data["name"],
                    account_data["secret"],
                    account_data["note"],
                )
                self.load_accounts()

                # 更新当前选中的账号
                updated_account = self.account_service.get_account(
                    self.selected_account["id"]
                )
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

        # 根据配置决定是否需要确认
        require_confirmation = self.config_manager.get(
            "security.require_confirmation_for_delete", True
        )

        if not require_confirmation or messagebox.askyesno(
            "确认删除", f"确定要删除账号 '{self.selected_account['name']}' 吗？"
        ):
            try:
                self.account_service.delete_account(self.selected_account["id"])
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
            defaultextension=".vault",
            filetypes=[("AuthVault 备份文件", "*.vault"), ("所有文件", "*.*")],
            initialfile=f"authvault_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.vault",
        )

        if filename:
            try:
                success, message = self.storage.backup(filename)
                if success:
                    messagebox.showinfo("成功", "数据备份成功！")
                    self.update_status(f"备份已保存: {filename}")
                else:
                    messagebox.showerror("错误", f"备份失败: {message}")
            except Exception as e:
                messagebox.showerror("错误", f"备份失败: {str(e)}")

    def restore_data(self):
        """恢复数据"""
        filename = filedialog.askopenfilename(
            filetypes=[("AuthVault 备份文件", "*.vault"), ("所有文件", "*.*")]
        )

        if filename:
            if messagebox.askyesno(
                "确认恢复", "恢复数据将覆盖当前所有账号，确定继续吗？"
            ):
                try:
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
                except Exception as e:
                    messagebox.showerror("错误", f"恢复失败: {str(e)}")

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
            # 解码二维码
            result = self.qr_decoder.decode_from_file(filename)
            if result and result.get("type") == "otpauth":
                # 导入账号
                account_id = self.account_service.import_from_otpauth_uri(
                    result["data"]
                )
                self.load_accounts()

                # 选中新添加的账号
                if self.account_list:
                    self.account_list.select_account(account_id)

                account = self.account_service.get_account(account_id)
                self.update_status(f"账号 '{account['name']}' 添加成功")
                messagebox.showinfo("成功", f"账号 '{account['name']}' 已添加！")
            else:
                messagebox.showerror("错误", "二维码中未找到有效的 OTP 信息")

        except QRCodeException as e:
            messagebox.showerror("错误", f"二维码解析失败:\n{str(e)}")
        except AccountException as e:
            messagebox.showerror("错误", f"添加账号失败:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")

    def screenshot_add(self):
        """截图识别二维码添加账号"""

        def on_result(result, error):
            """截图识别回调"""
            if error:
                messagebox.showerror("错误", f"识别失败:\n{error}")
                return

            if result and result.get("type") == "otpauth":
                try:
                    # 导入账号
                    account_id = self.account_service.import_from_otpauth_uri(
                        result["data"]
                    )
                    self.load_accounts()

                    # 选中新添加的账号
                    if self.account_list:
                        self.account_list.select_account(account_id)

                    account = self.account_service.get_account(account_id)
                    self.update_status(f"账号 '{account['name']}' 添加成功")
                    messagebox.showinfo("成功", f"账号 '{account['name']}' 已添加！")

                except AccountException as e:
                    messagebox.showerror("错误", f"添加账号失败:\n{str(e)}")
                except Exception as e:
                    messagebox.showerror("错误", f"处理失败: {str(e)}")
            else:
                messagebox.showerror("错误", "截图中未找到有效的 OTP 二维码")

        # 启动截图工具
        capture_and_decode(self.root, on_result, self.qr_decoder)

    def start_auto_update(self):
        """启动自动更新线程"""
        self.update_running = True
        self.update_thread = threading.Thread(target=self.auto_update_loop, daemon=True)
        self.update_thread.start()

    def auto_update_loop(self):
        """自动更新循环"""
        import time

        # 获取刷新间隔
        refresh_interval = (
            self.config_manager.get("ui.auto_refresh_interval", 1000) / 1000
        )

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

            time.sleep(refresh_interval)

    def update_status(self, message):
        """更新状态栏"""
        if self.status_label:
            self.status_label.config(text=message)

    def on_closing(self):
        """窗口关闭事件"""
        # 保存窗口配置
        try:
            geometry = self.root.geometry()
            # 解析几何字符串 "widthxheight+x+y"
            if "+" in geometry:
                size_part, pos_part = geometry.split("+", 1)
                width, height = size_part.split("x")
                x, y = (
                    pos_part.split("+", 1)
                    if "+" in pos_part
                    else pos_part.rsplit("-", 1)
                )

                self.config_manager.set_ui_config(
                    {
                        "window_size": {"width": int(width), "height": int(height)},
                        "window_position": {"x": int(x), "y": int(y)},
                    }
                )
            else:
                width, height = geometry.split("x")
                self.config_manager.set_ui_config(
                    {"window_size": {"width": int(width), "height": int(height)}}
                )

            self.config_manager.save_config()
        except Exception as e:
            print(f"保存配置失败: {e}")

        # 停止更新线程
        self.update_running = False
        if self.update_thread:
            self.update_thread.join(timeout=1)

        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()

    # 尝试设置图标
    try:
        root.iconbitmap("icon.ico")
    except:
        pass

    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
