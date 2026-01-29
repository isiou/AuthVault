import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import pyotp
import time
from datetime import datetime
import threading
import ctypes
from storage_manager import StorageManager
from qr_scanner import scan_qr_and_extract_2fa
from screenshot_tool import capture_and_decode

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

        # 当前选中的账号
        self.selected_account = None

        # 更新线程控制
        self.update_running = False
        self.update_thread = None

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

        # 顶部工具栏
        self.create_toolbar(main_container)

        # 中间主要内容区域
        content_frame = ttk.Frame(main_container)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)

        # 左侧：账号列表
        self.create_account_list(content_frame)

        # 右侧：验证码显示区域
        self.create_code_display(content_frame)

        # 底部状态栏
        self.create_status_bar(main_container)

    def create_toolbar(self, parent):
        """创建工具栏"""
        toolbar = ttk.Frame(parent)
        toolbar.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # 搜索框
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(search_frame, text="搜索: ").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT)

        # 按钮区域
        button_frame = ttk.Frame(toolbar)
        button_frame.pack(side=tk.RIGHT)

        ttk.Button(
            button_frame, text="添\u3000\u3000加", command=self.add_account, width=12
        ).pack(side=tk.LEFT, padx=1)
        ttk.Button(
            button_frame, text="编\u3000\u3000辑", command=self.edit_account, width=12
        ).pack(side=tk.LEFT, padx=1)
        ttk.Button(
            button_frame, text="删\u3000\u3000除", command=self.delete_account, width=12
        ).pack(side=tk.LEFT, padx=1)
        ttk.Button(
            button_frame, text="备\u3000\u3000份", command=self.backup_data, width=12
        ).pack(side=tk.LEFT, padx=1)
        ttk.Button(
            button_frame, text="导\u3000\u3000入", command=self.restore_data, width=12
        ).pack(side=tk.LEFT, padx=1)
        ttk.Button(
            button_frame, text="扫码添加", command=self.scan_qr_add, width=12
        ).pack(side=tk.LEFT, padx=1)
        ttk.Button(
            button_frame, text="截图添加", command=self.screenshot_add, width=12
        ).pack(side=tk.LEFT, padx=1)

    def create_account_list(self, parent):
        """创建账号列表"""
        list_frame = ttk.LabelFrame(parent, text="账号列表", padding="5")
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # 创建 Treeview
        columns = ("index", "name", "note")
        self.tree = ttk.Treeview(
            list_frame, columns=columns, show="headings", selectmode="browse"
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
            list_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self.on_account_select)

        # 双击编辑
        self.tree.bind("<Double-Button-1>", lambda e: self.edit_account())

    def create_code_display(self, parent):
        """创建验证码显示区域"""
        display_frame = ttk.LabelFrame(parent, text="验证码", padding="10")
        display_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        display_frame.columnconfigure(0, weight=1)

        # 账号信息
        info_frame = ttk.Frame(display_frame)
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        info_frame.columnconfigure(1, weight=1)

        ttk.Label(info_frame, text="账号: ").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.account_name_label = ttk.Label(
            info_frame, text="-", font=("Arial", 10, "bold")
        )
        self.account_name_label.grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(info_frame, text="备注:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.account_note_label = ttk.Label(info_frame, text="-")
        self.account_note_label.grid(row=1, column=1, sticky=tk.W, pady=2)

        # 分隔线
        ttk.Separator(display_frame, orient=tk.HORIZONTAL).grid(
            row=1, column=0, sticky=(tk.W, tk.E), pady=10
        )

        # 验证码显示
        code_frame = ttk.Frame(display_frame)
        code_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=20)
        code_frame.columnconfigure(0, weight=1)

        self.code_label = ttk.Label(
            code_frame,
            text="------",
            font=("Courier New", 48, "bold"),
            foreground="#2E86DE",
            anchor=tk.CENTER,
        )
        self.code_label.grid(row=0, column=0, pady=10)

        # 复制按钮
        ttk.Button(code_frame, text="复制验证码", command=self.copy_code).grid(
            row=1, column=0, pady=5
        )

        # 时间进度条
        progress_frame = ttk.Frame(display_frame)
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=10)
        progress_frame.columnconfigure(0, weight=1)

        self.time_label = ttk.Label(
            progress_frame, text="剩余时间: --s", font=("Arial", 10)
        )
        self.time_label.grid(row=0, column=0, pady=5)

        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="determinate", maximum=30
        )
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        # 密钥显示与隐藏
        key_frame = ttk.Frame(display_frame)
        key_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
        key_frame.columnconfigure(0, weight=1)

        self.show_key_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            key_frame,
            text="显示密钥",
            variable=self.show_key_var,
            command=self.toggle_key_display,
        ).grid(row=0, column=0, sticky=tk.W)

        self.key_label = ttk.Label(
            key_frame, text="", font=("Courier New", 9), foreground="#666"
        )
        self.key_label.grid(row=1, column=0, sticky=tk.W, pady=5)

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
        # 清空现有列表
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 加载账号
        accounts = self.storage.get_all_accounts()
        for idx, account in enumerate(accounts, 1):
            self.tree.insert(
                "",
                tk.END,
                iid=account["id"],
                values=(str(idx), account["name"], account["note"]),
            )

        self.update_status(f"已加载 {len(accounts)} 个账号")

    def on_search(self, *args):
        """搜索账号"""
        search_text = self.search_var.get().lower()

        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 重新加载过滤后的账号
        accounts = self.storage.get_all_accounts()
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

    def on_account_select(self, event):
        """账号选择事件"""
        selection = self.tree.selection()
        if not selection:
            self.selected_account = None
            self.clear_code_display()
            return

        account_id = selection[0]
        account = self.storage.get_account(account_id)

        if account:
            self.selected_account = account
            self.update_code_display()

    def update_code_display(self):
        """更新验证码显示"""
        if not self.selected_account:
            self.clear_code_display()
            return

        # 更新账号信息
        self.account_name_label.config(text=self.selected_account["name"])
        self.account_note_label.config(text=self.selected_account["note"] or "-")

        # 更新密钥显示
        self.toggle_key_display()

        # 生成验证码
        try:
            totp = pyotp.TOTP(self.selected_account["secret"])
            code = totp.now()
            remaining = totp.interval - (datetime.now().timestamp() % totp.interval)

            self.code_label.config(text=code)
            self.time_label.config(text=f"剩余时间: {int(remaining)}s")
            self.progress_bar["value"] = remaining
        except Exception as e:
            self.code_label.config(text="错误")
            self.update_status(f"生成验证码失败: {str(e)}")

    def clear_code_display(self):
        """清空验证码显示"""
        self.account_name_label.config(text="-")
        self.account_note_label.config(text="-")
        self.code_label.config(text="------")
        self.time_label.config(text="剩余时间: --s")
        self.progress_bar["value"] = 0
        self.key_label.config(text="")

    def toggle_key_display(self):
        """切换密钥显示"""
        if not self.selected_account:
            return

        if self.show_key_var.get():
            self.key_label.config(text=self.selected_account["secret"])
        else:
            self.key_label.config(text="*" * 20)

    def copy_code(self):
        """复制验证码到剪贴板"""
        if not self.selected_account:
            return

        code = self.code_label.cget("text")
        if code and code != "------":
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.update_status("验证码已复制到剪贴板")

    def add_account(self):
        """添加账号"""
        dialog = AccountDialog(self.root, "添加账号")
        if dialog.result:
            account_data = dialog.result
            success, message = self.storage.add_account(
                account_data["name"], account_data["secret"], account_data["note"]
            )

            if success:
                self.load_accounts()
                self.update_status("账号添加成功")
            else:
                messagebox.showerror("错误", message)

    def edit_account(self):
        """编辑账号"""
        if not self.selected_account:
            messagebox.showwarning("提示", "请先选择要编辑的账号")
            return

        dialog = AccountDialog(self.root, "编辑账号", self.selected_account)
        if dialog.result:
            account_data = dialog.result
            success, message = self.storage.update_account(
                self.selected_account["id"],
                account_data["name"],
                account_data["secret"],
                account_data["note"],
            )

            if success:
                self.load_accounts()
                self.selected_account = self.storage.get_account(
                    self.selected_account["id"]
                )
                self.update_code_display()
                self.update_status("账号更新成功")
            else:
                messagebox.showerror("错误", message)

    def delete_account(self):
        """删除账号"""
        if not self.selected_account:
            messagebox.showwarning("提示", "请先选择要删除的账号")
            return

        if messagebox.askyesno(
            "确认删除", f"确定要删除账号 '{self.selected_account['name']}' 吗？"
        ):
            success, message = self.storage.delete_account(self.selected_account["id"])

            if success:
                self.selected_account = None
                self.load_accounts()
                self.clear_code_display()
                self.update_status("账号删除成功")
            else:
                messagebox.showerror("错误", message)

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
                    self.clear_code_display()
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

        # 解析二维码
        info, error = scan_qr_and_extract_2fa(filename)

        if error:
            messagebox.showerror("错误", f"二维码解析失败: \n{error}")
            return

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

            # 添加账号
            success, message = self.storage.add_account(
                name, info["secret"], f"从二维码导入 - {info['account']}"
            )

            if success:
                self.load_accounts()
                self.update_status(f"账号 '{name}' 添加成功")
                messagebox.showinfo("成功", f"账号 '{name}' 已添加！")
            else:
                messagebox.showerror("错误", message)

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

                # 添加账号
                success, message = self.storage.add_account(
                    name, info["secret"], f"从截图导入 - {info['account']}"
                )

                if success:
                    self.load_accounts()
                    self.update_status(f"账号 '{name}' 添加成功")
                    messagebox.showinfo("成功", f"账号 '{name}' 已添加！")
                else:
                    messagebox.showerror("错误", message)

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
                if self.selected_account:
                    self.root.after(0, self.update_code_display)

                # 更新状态栏时间
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            messagebox.showwarning("提示", "密钥格式无效")
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
