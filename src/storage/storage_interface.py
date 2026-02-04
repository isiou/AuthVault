"""
存储接口定义
定义统一的存储操作接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class StorageInterface(ABC):
    """存储操作接口"""

    @abstractmethod
    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """获取所有账号"""
        pass

    @abstractmethod
    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取账号"""
        pass

    @abstractmethod
    def add_account(self, name: str, secret: str, note: str = "") -> str:
        """添加账号，返回账号ID"""
        pass

    @abstractmethod
    def update_account(
        self, account_id: str, name: str, secret: str, note: str = ""
    ) -> None:
        """更新账号"""
        pass

    @abstractmethod
    def delete_account(self, account_id: str) -> None:
        """删除账号"""
        pass

    @abstractmethod
    def backup(self, backup_file: str) -> tuple[bool, str]:
        """备份数据到文件"""
        pass

    @abstractmethod
    def restore(self, backup_file: str) -> tuple[bool, str]:
        """从备份文件恢复数据"""
        pass
