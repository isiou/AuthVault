"""
二维码处理服务
统一管理所有二维码相关操作，解耦各模块间的依赖
"""

import sys
import re
import os
from urllib.parse import urlparse, parse_qs, unquote
from typing import Optional, Tuple, Dict, Any
from PIL import Image
import numpy as np

# 添加路径处理，以便能够导入src模块
if __name__ == "__main__" or "src." not in __name__:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

try:
    from src.exceptions import (
        QRCodeException,
        QRCodeNotFoundError,
        InvalidQRCodeError,
        InvalidOTPAuthURIError,
    )
except ImportError:
    # 如果仍然无法导入，尝试相对导入
    from exceptions import (
        QRCodeException,
        QRCodeNotFoundError,
        InvalidQRCodeError,
        InvalidOTPAuthURIError,
    )

# 导入 cv2
try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# 导入 pyzbar
try:
    from pyzbar.pyzbar import decode as pyzbar_decode

    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
except Exception as e:
    # 处理DLL加载错误或其他系统相关错误
    print(f"Warning: pyzbar library initialization failed: {e}")
    PYZBAR_AVAILABLE = False


class QRCodeService:
    """二维码处理服务类"""

    def __init__(self):
        self.cv2_available = CV2_AVAILABLE
        self.pyzbar_available = PYZBAR_AVAILABLE

    def decode_from_file(self, image_path: str) -> str:
        """
        从文件解码二维码

        Args:
            image_path: 图片文件路径

        Returns:
            二维码内容字符串

        Raises:
            QRCodeNotFoundError: 未检测到二维码
            QRCodeException: 解码过程中的其他错误
        """
        # 优先使用 OpenCV
        if self.cv2_available:
            try:
                return self._decode_with_cv2(image_path)
            except QRCodeNotFoundError:
                pass  # 尝试备选方案
            except Exception as e:
                raise QRCodeException(f"OpenCV解码失败: {str(e)}")

        # 备选使用 pyzbar
        if self.pyzbar_available:
            try:
                return self._decode_with_pyzbar(image_path)
            except QRCodeNotFoundError:
                pass  # 尝试其他方案
            except Exception as e:
                raise QRCodeException(f"Pyzbar解码失败: {str(e)}")

        # 没有可用的解码库
        if not self.cv2_available and not self.pyzbar_available:
            raise QRCodeException("缺少二维码解码库，请安装 opencv-python 或 pyzbar")

        # 所有方法都失败
        raise QRCodeNotFoundError("未检测到二维码")

    def decode_from_image(self, image: Image.Image) -> str:
        """
        从PIL图像对象解码二维码

        Args:
            image: PIL图像对象

        Returns:
            二维码内容字符串

        Raises:
            QRCodeNotFoundError: 未检测到二维码
            QRCodeException: 解码过程中的其他错误
        """
        if self.cv2_available:
            try:
                # 将 PIL 图像转换为 OpenCV 格式
                cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                detector = cv2.QRCodeDetector()
                data, vertices, _ = detector.detectAndDecode(cv_image)

                if data:
                    return data
                raise QRCodeNotFoundError("未检测到二维码")
            except QRCodeNotFoundError:
                raise
            except Exception as e:
                raise QRCodeException(f"OpenCV解码失败: {str(e)}")

        if self.pyzbar_available:
            try:
                decoded_objects = pyzbar_decode(image)
                if decoded_objects:
                    return decoded_objects[0].data.decode("utf-8")
                raise QRCodeNotFoundError("未检测到二维码")
            except QRCodeNotFoundError:
                raise
            except Exception as e:
                raise QRCodeException(f"Pyzbar解码失败: {str(e)}")

        raise QRCodeException("缺少二维码解码库")

    def _decode_with_cv2(self, image_path: str) -> str:
        """使用 OpenCV 解码二维码"""
        image = cv2.imread(image_path)
        if image is None:
            raise QRCodeException("无法读取图片")

        detector = cv2.QRCodeDetector()
        data, vertices, _ = detector.detectAndDecode(image)

        if not data:
            raise QRCodeNotFoundError("未检测到二维码")

        return data

    def _decode_with_pyzbar(self, image_path: str) -> str:
        """使用 pyzbar 解码二维码"""
        image = Image.open(image_path)
        decoded_objects = pyzbar_decode(image)

        if not decoded_objects:
            raise QRCodeNotFoundError("未检测到二维码")

        return decoded_objects[0].data.decode("utf-8")

    def parse_otpauth_uri(self, uri: str) -> Dict[str, Any]:
        """
        解析 OTPAuth URI

        Args:
            uri: OTPAuth URI字符串

        Returns:
            包含解析结果的字典

        Raises:
            InvalidOTPAuthURIError: URI格式无效
        """
        try:
            parsed = urlparse(uri)

            if parsed.scheme != "otpauth":
                raise InvalidOTPAuthURIError("不是有效的 OTPAuth URI")

            # 获取类型
            otp_type = parsed.netloc

            # 获取标签
            label = unquote(parsed.path.lstrip("/"))

            # 解析查询参数
            params = parse_qs(parsed.query)

            # 提取密钥
            secret = params.get("secret", [None])[0]
            if not secret:
                raise InvalidOTPAuthURIError("未找到密钥参数")

            # 提取其他参数
            issuer = params.get("issuer", [None])[0]
            if issuer:
                issuer = unquote(issuer)

            # 提取账号
            if ":" in label:
                parts = label.split(":", 1)
                label_issuer = parts[0]
                account = parts[1]
                if not issuer:
                    issuer = label_issuer
            else:
                account = label

            # 其他可选参数
            algorithm = params.get("algorithm", ["SHA1"])[0]
            digits = params.get("digits", ["6"])[0]
            period = params.get("period", ["30"])[0]

            result = {
                "type": otp_type.upper(),
                "secret": secret.upper(),
                "issuer": issuer or "",
                "account": account,
                "algorithm": algorithm,
                "digits": int(digits),
                "period": int(period),
                "original_uri": uri,
            }

            return result

        except ValueError as e:
            raise InvalidOTPAuthURIError(f"参数格式错误: {str(e)}")
        except Exception as e:
            raise InvalidOTPAuthURIError(f"解析错误: {str(e)}")

    def extract_2fa_from_file(self, image_path: str) -> Dict[str, Any]:
        """
        从图片文件中提取2FA信息

        Args:
            image_path: 图片文件路径

        Returns:
            2FA信息字典

        Raises:
            QRCodeNotFoundError: 未检测到二维码
            InvalidQRCodeError: 不是2FA二维码
            InvalidOTPAuthURIError: URI格式无效
        """
        # 解码二维码
        qr_data = self.decode_from_file(image_path)

        # 检查是否是 otpauth URI
        if not qr_data.startswith("otpauth://"):
            raise InvalidQRCodeError(f"不是 2FA 二维码。内容: {qr_data}")

        # 解析 otpauth URI
        return self.parse_otpauth_uri(qr_data)

    def extract_2fa_from_image(self, image: Image.Image) -> Dict[str, Any]:
        """
        从PIL图像对象中提取2FA信息

        Args:
            image: PIL图像对象

        Returns:
            2FA信息字典

        Raises:
            QRCodeNotFoundError: 未检测到二维码
            InvalidQRCodeError: 不是2FA二维码
            InvalidOTPAuthURIError: URI格式无效
        """
        # 解码二维码
        qr_data = self.decode_from_image(image)

        # 检查是否是 otpauth URI
        if not qr_data.startswith("otpauth://"):
            raise InvalidQRCodeError(f"不是 2FA 二维码。内容: {qr_data}")

        # 解析 otpauth URI
        return self.parse_otpauth_uri(qr_data)


# 全局单例实例
_qr_service_instance = None


def get_qr_service() -> QRCodeService:
    """获取二维码服务单例实例"""
    global _qr_service_instance
    if _qr_service_instance is None:
        _qr_service_instance = QRCodeService()
    return _qr_service_instance
