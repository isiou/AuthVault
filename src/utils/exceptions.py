"""
自定义异常类定义
统一项目中的错误处理机制
"""


class AuthVaultException(Exception):
    """AuthVault应用的基础异常类"""

    pass


class StorageException(AuthVaultException):
    """存储相关异常"""

    pass


class AccountException(AuthVaultException):
    """账号管理相关异常"""

    pass


class QRCodeException(AuthVaultException):
    """二维码处理相关异常"""

    pass


class TOTPException(AuthVaultException):
    """TOTP相关异常"""

    pass


class ScreenshotException(AuthVaultException):
    """截图工具相关异常"""

    pass


class ValidationException(AuthVaultException):
    """数据验证相关异常"""

    pass


class ConfigException(AuthVaultException):
    """配置相关异常"""

    pass


class EncryptionException(StorageException):
    """加密解密相关异常"""

    pass


class AccountNotFoundError(AccountException):
    """账号未找到异常"""

    pass


class AccountAlreadyExistsError(AccountException):
    """账号已存在异常"""

    pass


class InvalidSecretError(ValidationException):
    """无效的TOTP密钥异常"""

    pass


class QRCodeNotFoundError(QRCodeException):
    """未检测到二维码异常"""

    pass


class InvalidQRCodeError(QRCodeException):
    """无效的二维码内容异常"""

    pass


class InvalidOTPAuthURIError(QRCodeException):
    """无效的OTPAuth URI异常"""

    pass
