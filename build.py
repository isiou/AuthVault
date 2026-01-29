import os
import sys
import shutil
import subprocess
from pathlib import Path

# 应用信息
APP_NAME = "AuthVault"
MAIN_SCRIPT = "gui_app.py"
ICON_FILE = "icon.ico"

INCLUDE_FILES = [
    "storage_manager.py",
    "qr_scanner.py",
    "screenshot_tool.py",
]

EXCLUDE_MODULES = []

# 需要的隐式导入
HIDDEN_IMPORTS = [
    "PIL",
    "PIL.Image",
    "PIL.ImageGrab",
    "PIL.ImageTk",
    "cv2",
    "numpy",
    "pyotp",
    "cryptography",
]


def clean_build():
    """清理构建目录"""
    print("清理旧的构建文件...")

    dirs_to_remove = ["build", "dist", "__pycache__"]

    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除: {dir_name}/")


def check_dependencies():
    """检查必要的依赖"""
    print("检查依赖...")

    required = ["pyotp", "cryptography", "cv2", "PIL", "numpy"]
    missing = []

    for module in required:
        try:
            __import__(module)
        except ImportError:
            print(f"{module} 缺失...")
            missing.append(module)

    if missing:
        print(f"缺少依赖: {', '.join(missing)}")
        return False

    return True


def build_exe():
    """构建可执行文件"""
    print("开始构建可执行文件...")

    # 检查图标文件
    icon_arg = []
    if os.path.exists(ICON_FILE):
        icon_arg = [f"--icon={ICON_FILE}"]
        print(f"使用图标: {ICON_FILE}")
    else:
        print(f"未找到图标文件: {ICON_FILE}")

    # 构建 PyInstaller 参数
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        f"--name={APP_NAME}",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
    ]

    # 添加图标
    args.extend(icon_arg)

    # 添加数据文件
    for file in INCLUDE_FILES:
        if os.path.exists(file):
            args.append(f"--add-data={file};.")

    # 添加隐式导入
    for module in HIDDEN_IMPORTS:
        args.append(f"--hidden-import={module}")

    # 添加排除模块
    for module in EXCLUDE_MODULES:
        args.append(f"--exclude-module={module}")

    # 主脚本
    args.append(MAIN_SCRIPT)

    print(f"执行命令: PyInstaller {APP_NAME}")

    result = subprocess.run(args)

    if result.returncode == 0:
        print("构建成功！")
        return True
    else:
        print("构建失败！")
        return False


def create_distribution():
    """创建发布目录"""
    print("创建发布目录...")

    dist_dir = Path("release")
    dist_dir.mkdir(exist_ok=True)

    exe_name = f"{APP_NAME}.exe"
    src_exe = Path("dist") / exe_name
    dest_exe = dist_dir / exe_name

    if src_exe.exists():
        shutil.copy(src_exe, dest_exe)
        print(f"已复制: {exe_name} -> release/")

        # 计算文件大小
        size_bytes = dest_exe.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        print(f"文件大小: {size_mb:.2f} MB")
    else:
        print(f"错误: 未找到 {src_exe}")
        return False

    print(f"\n发布目录: {dist_dir.absolute()}")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print(f"{APP_NAME} 打包工具")
    print("=" * 60)

    # 检查 PyInstaller
    try:
        import PyInstaller

        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 检查依赖
    if not check_dependencies():
        print("请先安装缺失的依赖后再运行打包！")
        sys.exit(1)

    # 清理旧文件
    clean_build()

    # 构建
    if build_exe():
        create_distribution()
        print("\n" + "=" * 60)
        print("打包完成！")
        print("=" * 60)
    else:
        print("\n打包失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
