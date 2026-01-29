# AuthVault

一个简洁高效的双因素身份验证（2FA）管理工具，提供图形化界面和安全的凭证存储。

## 功能特性

- 2FA 密钥管理 - 安全存储和管理 TOTP
- 图形化界面 - 直观的 Tkinter UI，易于使用
- 加密存储 - 使用加密技术保护敏感信息
- 实时更新 - 显示动态更新的一次性密码和倒计时

## 技术栈

- Python 3 - 核心语言
- Tkinter - GUI 框架
- PyOTP - TOTP 实现
- Cryptography - 加密库

## 安装

### 前置要求

- Python 3.7 或更高版本

### 依赖安装

```bash
pip install -r requirements.txt
```

## 使用

运行应用程序：

```bash
python gui_app.py
```

## 打包

使用 PyInstaller 构建可执行文件：

```bash
python build.py
```

## 项目结构

- `gui_app.py` - 主应用程序和 GUI 实现
- `storage_manager.py` - 凭证存储和管理模块
- `build.py` - PyInstaller 构建脚本
- `AuthVault.spec` - PyInstaller 配置文件

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
