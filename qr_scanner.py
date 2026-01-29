import sys
import re
from urllib.parse import urlparse, parse_qs, unquote

# 导入 cv2
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


def parse_otpauth_uri(uri):
    # 解析 otpauth URI
    try:
        parsed = urlparse(uri)

        if parsed.scheme != "otpauth":
            return None, "不是有效的 OTPAuth URI"

        # 获取类型
        otp_type = parsed.netloc

        # 获取标签
        label = unquote(parsed.path.lstrip("/"))

        # 解析查询参数
        params = parse_qs(parsed.query)

        # 提取密钥
        secret = params.get("secret", [None])[0]
        if not secret:
            return None, "未找到密钥参数"

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

        return result, None

    except Exception as e:
        return None, f"解析错误: {str(e)}"


def decode_qr_pyzbar(image_path):
    """使用 pyzbar 解码二维码"""
    try:
        image = Image.open(image_path)
        decoded_objects = decode(image)

        if not decoded_objects:
            return None, "未检测到二维码"

        # 返回第一个二维码的内容
        qr_data = decoded_objects[0].data.decode("utf-8")
        return qr_data, None

    except Exception as e:
        return None, f"解码失败: {str(e)}"


def decode_qr_cv2(image_path):
    """使用 OpenCV 解码二维码"""
    try:
        image = cv2.imread(image_path)
        if image is None:
            return None, "无法读取图片"

        detector = cv2.QRCodeDetector()
        data, vertices, _ = detector.detectAndDecode(image)

        if not data:
            return None, "未检测到二维码"

        return data, None

    except Exception as e:
        return None, f"解码失败: {str(e)}"


def decode_qr_image(image_path):
    """解码二维码图片"""
    # 优先使用 cv2
    if CV2_AVAILABLE:
        result, error = decode_qr_cv2(image_path)
        if result:
            return result, None

    # 备选使用 pyzbar
    if PYZBAR_AVAILABLE:
        result, error = decode_qr_pyzbar(image_path)
        if result:
            return result, None

    if not PYZBAR_AVAILABLE and not CV2_AVAILABLE:
        return None, "缺失解码库"

    return None, "无法解码二维码"


def scan_qr_and_extract_2fa(image_path):
    """
    扫描二维码并提取 2FA 信息
    """
    # 解码二维码
    qr_data, error = decode_qr_image(image_path)
    if error:
        return None, error

    # 检查是否是 otpauth URI
    if not qr_data.startswith("otpauth://"):
        return None, f"不是 2FA 二维码。内容: {qr_data}"

    # 解析 otpauth URI
    info, error = parse_otpauth_uri(qr_data)
    if error:
        return None, error

    return info, None
