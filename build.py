import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build():
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["*.spec"]

    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

    for pattern in files_to_remove:
        import glob

        for file in glob.glob(pattern):
            os.remove(file)


def build_exe():
    print("开始构建可执行文件...")

    # PyInstaller 参数
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=AuthVault",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--icon=icon.ico",
        "--add-data=storage_manager.py;.",
        "--optimize=2",
        "--exclude-module=matplotlib",
        "--exclude-module=numpy",
        "--exclude-module=pandas",
        "--exclude-module=scipy",
        "--exclude-module=PIL",
        "--exclude-module=cv2",
        "--exclude-module=torch",
        "--exclude-module=tensorflow",
        "gui_app.py",
    ]

    result = subprocess.run(args, capture_output=False)

    if result.returncode == 0:
        print("构建成功...")
        return True
    else:
        print("构建失败...")
        return False


def create_distribution():
    print("创建发布目录...")

    dist_dir = Path("release")
    dist_dir.mkdir(exist_ok=True)

    exe_name = "AuthVault.exe"
    src_exe = Path("dist") / exe_name

    if src_exe.exists():
        shutil.copy(src_exe, dist_dir / exe_name)

    # 计算文件大小
    exe_path = dist_dir / exe_name
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"发布文件大小: {size_mb:.2f} MB")

    print(f"发布目录已创建: {dist_dir.absolute()}")
    return True


def main():
    print("=" * 60)
    print("AuthVault - 打包工具")
    print("=" * 60)

    try:
        import PyInstaller

        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("正在安装 PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 清理
    clean_build()

    # 构建
    if build_exe():
        create_distribution()

        print("=" * 60)
        print("打包完成...")
        print("=" * 60)
        print("发布文件位于 release/ 目录...")
    else:
        print("打包失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
