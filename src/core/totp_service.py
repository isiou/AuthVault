"""
TOTP (Time-based One-Time Password) 服务
负责生成和管理双重认证码
"""

import pyotp
import time
import base64
import binascii
from typing import Dict, Any, List, Optional

try:
    from src.utils.exceptions import TOTPException
except ImportError:
    from utils.exceptions import TOTPException


class TOTPService:
    """TOTP 双重认证服务"""

    def __init__(self):
        self.interval = 30  # TOTP 间隔，默认30秒

    def normalize_secret(self, secret: str) -> str:
        """标准化密钥格式"""
        try:
            # 移除空格和换行符
            secret = secret.strip().replace(" ", "").replace("\n", "")

            # 如果是 base32 编码，确保长度是 8 的倍数
            if len(secret) % 8 != 0:
                secret = secret + "=" * (8 - len(secret) % 8)

            # 验证 base32 格式
            base64.b32decode(secret.upper())

            return secret.upper()

        except Exception as e:
            raise TOTPException(f"无效的密钥格式: {str(e)}")

    def generate_totp(self, secret: str) -> Dict[str, Any]:
        """生成 TOTP 验证码

        Args:
            secret: TOTP 密钥

        Returns:
            包含验证码和剩余时间的字典

        Raises:
            TOTPException: 生成失败时抛出
        """
        try:
            normalized_secret = self.normalize_secret(secret)
            totp = pyotp.TOTP(normalized_secret, interval=self.interval)

            # 生成当前验证码
            code = totp.now()

            # 计算剩余时间（秒）
            current_time = time.time()
            time_step = int(current_time // self.interval)
            next_step_time = (time_step + 1) * self.interval
            remaining_time = int(next_step_time - current_time)

            return {
                "code": code,
                "remaining_time": remaining_time,
                "total_time": self.interval,
            }

        except Exception as e:
            raise TOTPException(f"生成 TOTP 验证码失败: {str(e)}")

    def verify_totp(self, secret: str, token: str, window: int = 1) -> bool:
        """验证 TOTP 验证码

        Args:
            secret: TOTP 密钥
            token: 用户输入的验证码
            window: 时间窗口容错（允许前后几个时间段的验证码）

        Returns:
            验证是否成功

        Raises:
            TOTPException: 验证失败时抛出
        """
        try:
            normalized_secret = self.normalize_secret(secret)
            totp = pyotp.TOTP(normalized_secret, interval=self.interval)

            # 验证码格式检查
            if not token or len(token) != 6 or not token.isdigit():
                return False

            return totp.verify(token, valid_window=window)

        except Exception as e:
            raise TOTPException(f"验证 TOTP 验证码失败: {str(e)}")

    def get_qr_code_url(
        self, secret: str, account_name: str, issuer: str = "AuthVault"
    ) -> str:
        """获取二维码 URL

        Args:
            secret: TOTP 密钥
            account_name: 账户名
            issuer: 发行方名称

        Returns:
            二维码 URL

        Raises:
            TOTPException: 生成失败时抛出
        """
        try:
            normalized_secret = self.normalize_secret(secret)
            totp = pyotp.TOTP(normalized_secret)

            return totp.provisioning_uri(name=account_name, issuer_name=issuer)

        except Exception as e:
            raise TOTPException(f"生成二维码 URL 失败: {str(e)}")

    def get_remaining_time_percentage(self) -> float:
        """获取当前周期剩余时间百分比

        Returns:
            剩余时间百分比 (0.0 - 1.0)
        """
        try:
            current_time = time.time()
            time_step = int(current_time // self.interval)
            next_step_time = (time_step + 1) * self.interval
            remaining_time = next_step_time - current_time

            return remaining_time / self.interval

        except Exception:
            return 0.0

    def batch_generate_totp(
        self, accounts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """批量生成 TOTP 验证码

        Args:
            accounts: 账户列表，每个账户包含 id, name, secret 等字段

        Returns:
            包含验证码信息的账户列表
        """
        results = []

        for account in accounts:
            try:
                totp_info = self.generate_totp(account.get("secret", ""))
                account_result = account.copy()
                account_result.update(totp_info)
                results.append(account_result)

            except TOTPException as e:
                # 如果某个账户生成失败，记录错误但不中断整个批次
                account_result = account.copy()
                account_result.update(
                    {
                        "code": "ERROR",
                        "remaining_time": 0,
                        "total_time": self.interval,
                        "error": str(e),
                    }
                )
                results.append(account_result)

        return results
