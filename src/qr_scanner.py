"""
二维码扫描和解析模块 (向后兼容版本)
现在使用统一的QRCodeService
"""

import sys
import re
import os
from urllib.parse import urlparse, parse_qs, unquote
from typing import Tuple, Optional, Dict, Any

# 添加路径处理
if __name__ == "__main__" or "src." not in __name__:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

try:
    from src.qr_service import get_qr_service
    from src.exceptions import (
        QRCodeException,
        QRCodeNotFoundError,
        InvalidQRCodeError,
        InvalidOTPAuthURIError,
    )
except ImportError:
    from qr_service import get_qr_service
    from exceptions import (
        QRCodeException,
        QRCodeNotFoundError,
        InvalidQRCodeError,
        InvalidOTPAuthURIError,
    )

# 保持向后兼容的导入检查
try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# 导入 pyzbar
PYZBAR_AVAILABLE = False
try:
    from PIL import Image
    from pyzbar.pyzbar import decode

    PYZBAR_AVAILABLE = True
except ImportError:
    pass
except Exception:
    pass


def parse_otpauth_uri(uri: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    解析 otpauth URI (向后兼容函数)

    Args:
        uri: OTPAuth URI字符串

    Returns:
        (解析结果字典, 错误信息)
    """
    try:
        qr_service = get_qr_service()
        result = qr_service.parse_otpauth_uri(uri)
        return result, None
    except InvalidOTPAuthURIError as e:
        return None, str(e)
    except Exception as e:
        return None, f"解析错误: {str(e)}"


def decode_qr_pyzbar(image_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    使用 pyzbar 解码二维码 (向后兼容函数)

    Args:
        image_path: 图片路径

    Returns:
        (二维码内容, 错误信息)
    """
    try:
        qr_service = get_qr_service()
        if not qr_service.pyzbar_available:
            return None, "pyzbar库不可用"
        result = qr_service._decode_with_pyzbar(image_path)
        return result, None
    except QRCodeNotFoundError as e:
        return None, str(e)
    except Exception as e:
        return None, f"解码失败: {str(e)}"


def decode_qr_cv2(image_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    使用 OpenCV 解码二维码 (向后兼容函数)

    Args:
        image_path: 图片路径

    Returns:
        (二维码内容, 错误信息)
    """
    try:
        qr_service = get_qr_service()
        if not qr_service.cv2_available:
            return None, "OpenCV库不可用"
        result = qr_service._decode_with_cv2(image_path)
        return result, None
    except QRCodeNotFoundError as e:
        return None, str(e)
    except Exception as e:
        return None, f"解码失败: {str(e)}"


def decode_qr_image(image_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    解码二维码图片 (向后兼容函数)

    Args:
        image_path: 图片路径

    Returns:
        (二维码内容, 错误信息)
    """
    try:
        qr_service = get_qr_service()
        result = qr_service.decode_from_file(image_path)
        return result, None
    except QRCodeNotFoundError as e:
        return None, str(e)
    except Exception as e:
        return None, f"解码失败: {str(e)}"


def scan_qr_and_extract_2fa(
    image_path: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    扫描二维码并提取 2FA 信息 (向后兼容函数)

    Args:
        image_path: 图片路径

    Returns:
        (2FA信息字典, 错误信息)
    """
    try:
        qr_service = get_qr_service()
        result = qr_service.extract_2fa_from_file(image_path)
        return result, None
    except (QRCodeNotFoundError, InvalidQRCodeError, InvalidOTPAuthURIError) as e:
        return None, str(e)
    except Exception as e:
        return None, f"处理失败: {str(e)}"
