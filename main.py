import pyotp
import time
import sys
from datetime import datetime


def get_current_2fa_code(secret_key):
    """
    获取当前的 2FA 代码和剩余时间
    """
    try:
        # 创建 TOTP 对象
        totp = pyotp.TOTP(secret_key)

        # 获取当前时刻的验证码
        current_code = totp.now()

        # 计算过期时间
        # 默认周期 30s
        time_remaining = totp.interval - (datetime.now().timestamp() % totp.interval)

        return current_code, int(time_remaining)

    except Exception as e:
        return None, 0


def generate_progress_bar(remaining, total=30, width=30):
    """
    字符进度条生成
    """
    percent = remaining / total
    filled_length = int(width * percent)
    bar = "#" * filled_length + "." * (width - filled_length)
    return f"[{bar}]"


if __name__ == "__main__":
    # 示例 2FA 密钥
    TEST_SECRET = "333BHZUNYOZEJ5LB"

    print("=" * 70)
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"当前密钥: {TEST_SECRET}")
    print("=" * 70)

    try:
        last_code = None

        while True:
            code, remaining = get_current_2fa_code(TEST_SECRET)

            if code:
                if last_code and code != last_code:
                    pass
                last_code = code

                # 生成进度条
                progress = generate_progress_bar(remaining)

                sys.stdout.write(f"\r当前验证码: {code}  {progress} {remaining:>2}s")

                # 强制刷新缓冲区
                sys.stdout.flush()

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n" + "-" * 70)
        print("正在结束程序...")
        print("-" * 70)
        sys.exit(0)
