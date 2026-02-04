"""
账户管理服务
负责账户的业务逻辑处理
"""

from typing import List, Dict, Any, Optional
import pyotp
import re

try:
    from src.storage.storage_interface import StorageInterface
    from src.core.totp_service import TOTPService
    from src.utils.exceptions import (
        AccountException,
        AccountNotFoundError,
        AccountAlreadyExistsError,
        TOTPException,
    )
except ImportError:
    from storage.storage_interface import StorageInterface
    from core.totp_service import TOTPService
    from utils.exceptions import (
        AccountException,
        AccountNotFoundError,
        AccountAlreadyExistsError,
        TOTPException,
    )


class AccountService:
    """账户管理服务"""

    def __init__(self, storage: StorageInterface, totp_service: TOTPService):
        self.storage = storage
        self.totp_service = totp_service

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        """获取所有账户"""
        return self.storage.get_all_accounts()

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取账户"""
        return self.storage.get_account(account_id)

    def add_account(self, name: str, secret: str, note: str = "") -> str:
        """添加新账户

        Args:
            name: 账户名称
            secret: TOTP密钥
            note: 备注信息

        Returns:
            新创建账户的ID

        Raises:
            AccountException: 参数验证失败
            AccountAlreadyExistsError: 账户名称已存在
        """
        # 参数验证
        self._validate_account_data(name, secret)

        # 标准化密钥
        normalized_secret = self.totp_service.normalize_secret(secret)

        return self.storage.add_account(name.strip(), normalized_secret, note.strip())

    def update_account(
        self, account_id: str, name: str, secret: str, note: str = ""
    ) -> None:
        """更新账户信息

        Args:
            account_id: 账户ID
            name: 账户名称
            secret: TOTP密钥
            note: 备注信息

        Raises:
            AccountException: 参数验证失败
            AccountNotFoundError: 账户不存在
            AccountAlreadyExistsError: 账户名称已存在
        """
        # 参数验证
        self._validate_account_data(name, secret)

        # 标准化密钥
        normalized_secret = self.totp_service.normalize_secret(secret)

        self.storage.update_account(
            account_id, name.strip(), normalized_secret, note.strip()
        )

    def delete_account(self, account_id: str) -> None:
        """删除账户

        Args:
            account_id: 账户ID

        Raises:
            AccountNotFoundError: 账户不存在
        """
        self.storage.delete_account(account_id)

    def validate_secret(self, secret: str) -> bool:
        """验证TOTP密钥是否有效

        Args:
            secret: TOTP密钥

        Returns:
            密钥是否有效
        """
        try:
            self.totp_service.normalize_secret(secret)
            return True
        except TOTPException:
            return False

    def generate_totp_for_account(self, account_id: str) -> Dict[str, Any]:
        """为指定账户生成TOTP验证码

        Args:
            account_id: 账户ID

        Returns:
            包含验证码信息的字典

        Raises:
            AccountNotFoundError: 账户不存在
            TOTPException: 生成验证码失败
        """
        account = self.storage.get_account(account_id)
        if not account:
            raise AccountNotFoundError(f"账户ID '{account_id}' 不存在")

        return self.totp_service.generate_totp(account["secret"])

    def get_accounts_with_totp(self) -> List[Dict[str, Any]]:
        """获取所有账户及其TOTP验证码

        Returns:
            包含TOTP验证码的账户列表
        """
        accounts = self.storage.get_all_accounts()
        return self.totp_service.batch_generate_totp(accounts)

    def search_accounts(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索账户

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的账户列表
        """
        if not keyword:
            return self.get_all_accounts()

        keyword = keyword.lower().strip()
        accounts = self.get_all_accounts()

        # 搜索账户名称和备注
        matching_accounts = []
        for account in accounts:
            if (
                keyword in account.get("name", "").lower()
                or keyword in account.get("note", "").lower()
            ):
                matching_accounts.append(account)

        return matching_accounts

    def get_account_statistics(self) -> Dict[str, Any]:
        """获取账户统计信息

        Returns:
            统计信息字典
        """
        accounts = self.get_all_accounts()

        return {
            "total_accounts": len(accounts),
            "accounts_with_notes": len(
                [a for a in accounts if a.get("note", "").strip()]
            ),
            "creation_dates": [
                a.get("created_at") for a in accounts if a.get("created_at")
            ],
        }

    def import_from_otpauth_uri(self, uri: str) -> str:
        """从otpauth URI导入账户

        Args:
            uri: otpauth://totp/...格式的URI

        Returns:
            创建的账户ID

        Raises:
            AccountException: URI格式无效或解析失败
        """
        try:
            # 解析 otpauth URI
            parsed_data = self._parse_otpauth_uri(uri)

            # 生成唯一的账户名称（如果已存在）
            base_name = parsed_data["name"]
            name = base_name
            counter = 1

            while any(acc["name"] == name for acc in self.get_all_accounts()):
                name = f"{base_name} ({counter})"
                counter += 1

            # 创建账户
            return self.add_account(
                name=name,
                secret=parsed_data["secret"],
                note=parsed_data.get("issuer", ""),
            )

        except Exception as e:
            raise AccountException(f"导入 OTP URI 失败: {str(e)}")

    def _validate_account_data(self, name: str, secret: str) -> None:
        """验证账户数据

        Args:
            name: 账户名称
            secret: TOTP密钥

        Raises:
            AccountException: 验证失败
        """
        # 验证名称
        if not name or not name.strip():
            raise AccountException("账户名称不能为空")

        if len(name.strip()) > 100:
            raise AccountException("账户名称过长（最多100个字符）")

        # 验证密钥
        if not secret or not secret.strip():
            raise AccountException("TOTP密钥不能为空")

        # 验证密钥格式
        try:
            self.totp_service.normalize_secret(secret)
        except TOTPException as e:
            raise AccountException(f"密钥格式无效: {str(e)}")

    def _parse_otpauth_uri(self, uri: str) -> Dict[str, Any]:
        """解析otpauth URI

        Args:
            uri: otpauth URI字符串

        Returns:
            解析后的数据字典

        Raises:
            AccountException: URI格式无效
        """
        # 基本格式检查
        if not uri.startswith("otpauth://totp/"):
            raise AccountException("不是有效的 TOTP URI")

        try:
            from urllib.parse import urlparse, parse_qs, unquote

            parsed = urlparse(uri)
            params = parse_qs(parsed.query)

            # 提取密钥
            secret = params.get("secret", [None])[0]
            if not secret:
                raise AccountException("URI中缺少密钥参数")

            # 提取账户名称（从path中提取）
            path = unquote(parsed.path)
            if path.startswith("/"):
                path = path[1:]  # 移除开头的斜杠

            # 如果路径包含冒号，分离发行方和账户名
            if ":" in path:
                issuer, account = path.split(":", 1)
            else:
                issuer = params.get("issuer", [None])[0] or ""
                account = path

            if not account:
                raise AccountException("URI中缺少账户名")

            return {"name": account, "secret": secret, "issuer": issuer}

        except Exception as e:
            raise AccountException(f"解析 OTP URI 失败: {str(e)}")
