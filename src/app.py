"""
AuthVault - 双重认证管理器
主应用程序入口文件
"""

import tkinter as tk
import sys
import os

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from src.ui.main_window import MainWindow
except ImportError:
    from ui.main_window import MainWindow


def main():
    """主函数"""
    # 创建根窗口
    root = tk.Tk()

    # 尝试设置应用图标
    try:
        icon_path = os.path.join(current_dir, "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass

    # 创建主窗口
    try:
        app = MainWindow(root)

        # 启动主循环
        root.mainloop()

    except Exception as e:
        # 如果出现严重错误，显示错误消息
        import tkinter.messagebox as messagebox

        messagebox.showerror(
            "启动错误",
            f"应用程序启动失败:\n{str(e)}\n\n"
            f"请检查程序安装是否完整，或联系技术支持。",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
