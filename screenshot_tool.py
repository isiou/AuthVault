import tkinter as tk
from PIL import Image, ImageGrab, ImageTk
import ctypes


class ScreenshotTool:
    """屏幕截图工具类"""

    def __init__(self, callback=None):
        """
        初始化截图工具
        """
        self.callback = callback
        self.screenshot_window = None
        self.float_window = None
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        self.screenshot_image = None
        self.photo_image = None

    def start(self, parent_window=None):
        # 保存父窗口引用
        self.parent_window = parent_window
        if parent_window:
            parent_window.withdraw()
            parent_window.after(300, self._show_float_window)
        else:
            self._show_float_window()

    def _show_float_window(self):
        # 创建悬浮窗
        if self.parent_window:
            self.float_window = tk.Toplevel(self.parent_window)
        else:
            self.float_window = tk.Toplevel()

        self.float_window.title("截图")
        self.float_window.attributes("-topmost", True)
        self.float_window.resizable(False, False)

        # 简约尺寸
        win_width = 300
        win_height = 100

        # 居中显示
        self.float_window.update_idletasks()
        screen_width = self.float_window.winfo_screenwidth()
        x = (screen_width - win_width) // 2
        self.float_window.geometry(f"{win_width}x{win_height}+{x}+80")

        self.float_window.lift()
        self.float_window.focus_force()

        # 简约布局
        frame = tk.Frame(self.float_window, padx=15, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="框选屏幕上的二维码").pack(pady=(0, 10))

        btn_frame = tk.Frame(frame)
        btn_frame.pack()

        tk.Button(btn_frame, text="开始", command=self._start_capture, width=8).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(btn_frame, text="取消", command=self._cancel, width=8).pack(
            side=tk.LEFT, padx=5
        )

        self.float_window.bind("<Escape>", lambda e: self._cancel())
        self.float_window.protocol("WM_DELETE_WINDOW", self._cancel)

    def _start_capture(self):
        """开始截图"""
        # 关闭悬浮窗
        if self.float_window:
            self.float_window.destroy()
            self.float_window = None

        # 等待悬浮窗消失后再截图
        if self.parent_window:
            self.parent_window.after(150, self._capture_screen)
        else:
            import time

            time.sleep(0.15)
            self._capture_screen()

    def _capture_screen(self):
        """截取整个屏幕并显示选择界面"""
        # 截取整个屏幕
        self.screenshot_image = ImageGrab.grab(all_screens=False)

        # 保存原始截图尺寸
        self.original_width = self.screenshot_image.width
        self.original_height = self.screenshot_image.height

        # 获取屏幕逻辑尺寸
        try:
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
        except Exception:
            screen_width = self.original_width
            screen_height = self.original_height

        # 创建全屏窗口用于选择区域
        self.screenshot_window = tk.Toplevel()
        self.screenshot_window.overrideredirect(True)
        self.screenshot_window.attributes("-topmost", True)
        self.screenshot_window.configure(cursor="cross")

        # 设置窗口尺寸为屏幕逻辑尺寸
        self.screenshot_window.geometry(f"{screen_width}x{screen_height}+0+0")
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 计算缩放比例
        self.scale_x = self.original_width / self.screen_width
        self.scale_y = self.original_height / self.screen_height

        # 将截图缩放到显示尺寸用于预览
        if (
            self.original_width != self.screen_width
            or self.original_height != self.screen_height
        ):
            self.display_image = self.screenshot_image.resize(
                (self.screen_width, self.screen_height), Image.Resampling.LANCZOS
            )
        else:
            self.display_image = self.screenshot_image

        # 将截图作为背景
        self.photo_image = ImageTk.PhotoImage(self.display_image)

        self.canvas = tk.Canvas(
            self.screenshot_window,
            width=self.screen_width,
            height=self.screen_height,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 显示截图
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_image)

        # 添加半透明遮罩
        self.overlay = self.canvas.create_rectangle(
            0,
            0,
            self.screen_width,
            self.screen_height,
            fill="#1a1a2e",
            stipple="gray75",
            outline="",
        )

        # 提示文字
        self.canvas.create_text(
            self.screen_width // 2,
            32,
            text="按住鼠标拖动选择二维码区域，右键取消",
            fill="#ffffff",
            font=(None, 16, "bold"),
        )

        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

        # 绑定 ESC 取消
        self.screenshot_window.bind("<Escape>", lambda e: self._cancel())
        self.screenshot_window.bind("<Key>", self._on_key)
        self.canvas.bind("<Escape>", lambda e: self._cancel())
        self.canvas.bind("<Key>", self._on_key)

        # 鼠标进入或移动时获取焦点
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())
        self.canvas.bind("<Motion>", self._on_motion)

        # 右键取消
        self.canvas.bind("<ButtonPress-3>", lambda e: self._cancel())

        # 强制获取焦点以接收键盘事件
        self.screenshot_window.focus_force()
        self.screenshot_window.grab_set()
        self.canvas.focus_set()

    def _on_key(self, event):
        """处理键盘事件"""
        if event.keysym == "Escape":
            self._cancel()

    def _on_motion(self, event):
        """鼠标移动时确保焦点"""
        if self.canvas:
            self.canvas.focus_set()

    def _on_mouse_down(self, event):
        """鼠标按下"""
        self.start_x = event.x
        self.start_y = event.y

        # 创建选择矩形
        if self.rect_id:
            self.canvas.delete(self.rect_id)

        self.rect_id = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="#4FC3F7",
            width=2,
        )

    def _on_mouse_move(self, event):
        """鼠标移动"""
        if self.rect_id:
            self.canvas.coords(
                self.rect_id, self.start_x, self.start_y, event.x, event.y
            )

    def _on_mouse_up(self, event):
        """鼠标释放"""
        end_x = event.x
        end_y = event.y

        # 确保坐标正确
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        # 检查选择区域是否太小
        if x2 - x1 < 10 or y2 - y1 < 10:
            return

        # 将显示坐标转换为原始截图坐标
        crop_x1 = int(x1 * self.scale_x)
        crop_y1 = int(y1 * self.scale_y)
        crop_x2 = int(x2 * self.scale_x)
        crop_y2 = int(y2 * self.scale_y)

        # 从原始截图裁剪选中区域
        cropped_image = self.screenshot_image.crop((crop_x1, crop_y1, crop_x2, crop_y2))

        # 关闭截图窗口
        if self.screenshot_window:
            try:
                self.screenshot_window.destroy()
            except:
                pass
            self.screenshot_window = None

        # 显示父窗口
        if self.parent_window:
            try:
                self.parent_window.deiconify()
                self.parent_window.lift()
                self.parent_window.focus_force()
            except:
                pass

        # 调用回调
        if self.callback:
            self.callback(cropped_image)

    def _cancel(self):
        """取消截图"""
        if self.float_window:
            try:
                self.float_window.destroy()
            except:
                pass
            self.float_window = None

        if self.screenshot_window:
            try:
                self.screenshot_window.destroy()
            except:
                pass
            self.screenshot_window = None

        # 显示父窗口
        if self.parent_window:
            try:
                self.parent_window.deiconify()
                self.parent_window.lift()
                self.parent_window.focus_force()
            except:
                pass


def capture_and_decode(parent_window, callback):
    """
    截图并解码二维码
    """

    def on_capture(image):
        """截图完成回调"""
        from qr_scanner import parse_otpauth_uri

        try:
            import cv2
            import numpy as np

            # 将 PIL 图像转换为 OpenCV 格式
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # 解码二维码
            detector = cv2.QRCodeDetector()
            data, vertices, _ = detector.detectAndDecode(cv_image)

            if not data:
                callback(None, "未检测到二维码，请确保二维码完整清晰")
                return

            # 检查是否是 otpauth URI
            if not data.startswith("otpauth://"):
                callback(None, f"不是 2FA 二维码\n内容: {data}")
                return

            # 解析 URI
            info, error = parse_otpauth_uri(data)
            callback(info, error)

        except Exception as e:
            callback(None, f"处理失败: {str(e)}")

    # 创建截图工具并启动
    tool = ScreenshotTool(callback=on_capture)
    tool.start(parent_window)


if __name__ == "__main__":
    # 测试截图功能
    def on_result(info, error):
        if error:
            print(f"错误: {error}")
        else:
            print(f"成功: {info}")
        root.destroy()

    root = tk.Tk()
    root.title("截图测试")
    root.geometry("300x100")

    tk.Button(
        root, text="截图识别二维码", command=lambda: capture_and_decode(root, on_result)
    ).pack(pady=30)

    root.mainloop()
