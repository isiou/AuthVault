"""
配置管理器
负责应用程序配置的加载、保存和管理
"""

import os
import json
import sys
from typing import Dict, Any, Optional

try:
    from src.utils.exceptions import ConfigException
except ImportError:
    from utils.exceptions import ConfigException


def get_config_dir():
    """获取配置文件目录"""
    if sys.platform == "win32":
        # Windows 系统
        base_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        config_dir = os.path.join(base_dir, "AuthVault")
    else:
        # Linux 或 Mac 系统
        config_dir = os.path.join(os.path.expanduser("~"), ".authvault")

    # 确保目录存在
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    return config_dir


class ConfigManager:
    """配置管理器"""

    # 默认配置
    DEFAULT_CONFIG = {
        "ui": {
            "theme": "default",
            "window_size": {"width": 800, "height": 600},
            "window_position": {"x": None, "y": None},
            "font_size": 10,
            "auto_refresh_interval": 1000,  # 毫秒
            "show_remaining_time": True,
            "show_account_notes": True,
            "compact_mode": False,
        },
        "security": {
            "auto_lock_timeout": 300,  # 秒，0表示不自动锁定
            "require_confirmation_for_delete": True,
            "hide_codes_by_default": False,
            "clipboard_timeout": 30,  # 秒，0表示不自动清除
        },
        "backup": {
            "auto_backup": False,
            "backup_interval": 7,  # 天
            "backup_location": "",
            "max_backup_files": 5,
        },
        "general": {
            "startup_behavior": "normal",  # "normal", "minimized", "hidden"
            "check_updates": True,
            "language": "zh-CN",
            "enable_logging": True,
            "log_level": "INFO",
        },
    }

    def __init__(self, config_file: Optional[str] = None):
        """初始化配置管理器

        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.config_dir = get_config_dir()
        self.config_file = config_file or os.path.join(self.config_dir, "config.json")
        self._config = self.DEFAULT_CONFIG.copy()
        self.load_config()

    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    user_config = json.load(f)

                # 深度合并配置
                self._config = self._merge_config(
                    self.DEFAULT_CONFIG.copy(), user_config
                )
            else:
                # 如果配置文件不存在，创建默认配置文件
                self.save_config()

        except Exception as e:
            raise ConfigException(f"加载配置文件失败: {str(e)}")

    def save_config(self) -> None:
        """保存配置文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)

        except Exception as e:
            raise ConfigException(f"保存配置文件失败: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键，支持点分隔的嵌套键，如 "ui.theme"
            default: 默认值

        Returns:
            配置值
        """
        try:
            keys = key.split(".")
            value = self._config

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value

        except Exception:
            return default

    def set(self, key: str, value: Any) -> None:
        """设置配置值

        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
        """
        try:
            keys = key.split(".")
            config = self._config

            # 导航到目标位置
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # 设置值
            config[keys[-1]] = value

        except Exception as e:
            raise ConfigException(f"设置配置值失败: {str(e)}")

    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return self.get("ui", {})

    def set_ui_config(self, config: Dict[str, Any]) -> None:
        """设置UI配置"""
        self.set("ui", {**self.get("ui", {}), **config})

    def get_security_config(self) -> Dict[str, Any]:
        """获取安全配置"""
        return self.get("security", {})

    def set_security_config(self, config: Dict[str, Any]) -> None:
        """设置安全配置"""
        self.set("security", {**self.get("security", {}), **config})

    def get_backup_config(self) -> Dict[str, Any]:
        """获取备份配置"""
        return self.get("backup", {})

    def set_backup_config(self, config: Dict[str, Any]) -> None:
        """设置备份配置"""
        self.set("backup", {**self.get("backup", {}), **config})

    def get_general_config(self) -> Dict[str, Any]:
        """获取通用配置"""
        return self.get("general", {})

    def set_general_config(self, config: Dict[str, Any]) -> None:
        """设置通用配置"""
        self.set("general", {**self.get("general", {}), **config})

    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        self._config = self.DEFAULT_CONFIG.copy()
        self.save_config()

    def export_config(self, export_file: str) -> None:
        """导出配置到文件

        Args:
            export_file: 导出文件路径
        """
        try:
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)

        except Exception as e:
            raise ConfigException(f"导出配置失败: {str(e)}")

    def import_config(self, import_file: str) -> None:
        """从文件导入配置

        Args:
            import_file: 导入文件路径
        """
        try:
            with open(import_file, "r", encoding="utf-8") as f:
                imported_config = json.load(f)

            # 合并配置（保持默认配置的结构）
            self._config = self._merge_config(
                self.DEFAULT_CONFIG.copy(), imported_config
            )
            self.save_config()

        except Exception as e:
            raise ConfigException(f"导入配置失败: {str(e)}")

    def get_config_file_path(self) -> str:
        """获取配置文件路径"""
        return self.config_file

    def get_config_dir_path(self) -> str:
        """获取配置目录路径"""
        return self.config_dir

    def _merge_config(self, base: Dict, overlay: Dict) -> Dict:
        """深度合并配置字典

        Args:
            base: 基础配置
            overlay: 覆盖配置

        Returns:
            合并后的配置
        """
        result = base.copy()

        for key, value in overlay.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value

        return result
