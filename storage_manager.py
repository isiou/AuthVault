import json
import os
import uuid
import sys
from datetime import datetime
from cryptography.fernet import Fernet

# 应用名称
APP_NAME = "AuthVault"

# 数据文件名
DATA_FILE = "data.vault"
KEY_FILE = "secret.key"


def get_app_data_dir():
    """
    获取应用数据目录
    Windows: %LOCALAPPDATA%/AuthVault/
    Linux/Mac: ~/.authvault/
    """
    if sys.platform == "win32":
        # Windows 系统
        base_dir = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        app_dir = os.path.join(base_dir, APP_NAME)
    else:
        # Linux 或 Mac 系统
        app_dir = os.path.join(os.path.expanduser("~"), f".{APP_NAME.lower()}")

    # 确保目录存在
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)

    return app_dir


class StorageManager:
    """存储管理器类"""

    def __init__(self, data_file=None, key_file=None):
        # 获取应用数据目录
        app_dir = get_app_data_dir()

        # 设置文件路径
        self.data_file = data_file or os.path.join(app_dir, DATA_FILE)
        self.key_file = key_file or os.path.join(app_dir, KEY_FILE)
        self.cipher = None

        # 检查旧文件并迁移
        self._migrate_old_files()

        # 初始化加密
        self._init_encryption()

        # 确保数据文件存在
        if not os.path.exists(self.data_file):
            self._save_data({"accounts": []})

    def _migrate_old_files(self):
        """迁移旧版本的数据文件"""
        # 旧文件路径
        if getattr(sys, "frozen", False):
            # 打包后的 exe
            exe_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境
            exe_dir = os.path.dirname(os.path.abspath(__file__))

        old_data_file = os.path.join(exe_dir, "accounts.dat")
        old_key_file = os.path.join(exe_dir, ".key")

        if os.path.exists(self.key_file) and os.path.exists(self.data_file):
            return

        # 迁移密钥文件
        if os.path.exists(old_key_file) and not os.path.exists(self.key_file):
            try:
                import shutil

                shutil.copy2(old_key_file, self.key_file)
            except Exception as e:
                return None

        # 迁移数据文件
        if os.path.exists(old_data_file) and not os.path.exists(self.data_file):
            try:
                import shutil

                shutil.copy2(old_data_file, self.data_file)
            except Exception as e:
                return None

    def get_data_dir(self):
        """获取数据存储目录"""
        return os.path.dirname(self.data_file)

    def get_data_file_path(self):
        """获取数据文件完整路径"""
        return self.data_file

    def _init_encryption(self):
        """初始化加密"""
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
        else:
            with open(self.key_file, "rb") as f:
                key = f.read()

        self.cipher = Fernet(key)

    def _load_data(self):
        """加载数据"""
        try:
            with open(self.data_file, "rb") as f:
                encrypted_data = f.read()

            if not encrypted_data:
                return {"accounts": []}

            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode("utf-8"))
        except Exception as e:
            print(f"加载数据失败: {e}")
            return {"accounts": []}

    def _save_data(self, data):
        """保存数据"""
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode("utf-8"))

            with open(self.data_file, "wb") as f:
                f.write(encrypted_data)

            return True
        except Exception as e:
            print(f"保存数据失败: {e}")
            return False

    def get_all_accounts(self):
        """获取所有账号"""
        data = self._load_data()
        return data.get("accounts", [])

    def get_account(self, account_id):
        """根据 ID 获取账号"""
        accounts = self.get_all_accounts()
        for account in accounts:
            if account["id"] == account_id:
                return account
        return None

    def add_account(self, name, secret, note=""):
        """添加账号"""
        try:
            data = self._load_data()

            # 检查账号名是否已存在
            for account in data["accounts"]:
                if account["name"] == name:
                    return False, "账号名称已存在"

            # 创建新账号
            new_account = {
                "id": str(uuid.uuid4()),
                "name": name,
                "secret": secret,
                "note": note,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            data["accounts"].append(new_account)

            if self._save_data(data):
                return True, "添加成功"
            else:
                return False, "保存失败"

        except Exception as e:
            return False, str(e)

    def update_account(self, account_id, name, secret, note=""):
        """更新账号"""
        try:
            data = self._load_data()

            # 查找账号
            account_found = False
            for account in data["accounts"]:
                if account["id"] == account_id:
                    # 检查新名称是否与其他账号冲突
                    if account["name"] != name:
                        for other_account in data["accounts"]:
                            if (
                                other_account["id"] != account_id
                                and other_account["name"] == name
                            ):
                                return False, "账号名称已存在"

                    # 更新账号信息
                    account["name"] = name
                    account["secret"] = secret
                    account["note"] = note
                    account["updated_at"] = datetime.now().isoformat()
                    account_found = True
                    break

            if not account_found:
                return False, "账号不存在"

            if self._save_data(data):
                return True, "更新成功"
            else:
                return False, "保存失败"

        except Exception as e:
            return False, str(e)

    def delete_account(self, account_id):
        """删除账号"""
        try:
            data = self._load_data()

            # 过滤掉要删除的账号
            original_count = len(data["accounts"])
            data["accounts"] = [
                acc for acc in data["accounts"] if acc["id"] != account_id
            ]

            if len(data["accounts"]) == original_count:
                return False, "账号不存在"

            if self._save_data(data):
                return True, "删除成功"
            else:
                return False, "保存失败"

        except Exception as e:
            return False, str(e)

    def backup(self, backup_file):
        """备份数据到文件"""
        try:
            data = self._load_data()

            # 创建备份数据
            backup_data = {
                "backup_time": datetime.now().isoformat(),
                "version": "1.0",
                "data": data,
            }

            # 加密备份数据
            json_data = json.dumps(backup_data, ensure_ascii=False, indent=2)
            encrypted_data = self.cipher.encrypt(json_data.encode("utf-8"))

            with open(backup_file, "wb") as f:
                f.write(encrypted_data)

            return True, "备份成功"

        except Exception as e:
            return False, str(e)

    def restore(self, backup_file):
        """从备份文件恢复数据"""
        try:
            with open(backup_file, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.cipher.decrypt(encrypted_data)
            backup_data = json.loads(decrypted_data.decode("utf-8"))

            # 提取实际数据
            if "data" in backup_data:
                data = backup_data["data"]
            else:
                data = backup_data

            # 保存恢复的数据
            if self._save_data(data):
                return True, "恢复成功"
            else:
                return False, "保存失败"

        except Exception as e:
            return False, f"恢复失败: {str(e)}"

    def export_plain(self, export_file):
        try:
            data = self._load_data()
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True, "导出成功"
        except Exception as e:
            return False, str(e)

    def import_plain(self, import_file):
        try:
            with open(import_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if self._save_data(data):
                return True, "导入成功"
            else:
                return False, "保存失败"
        except Exception as e:
            return False, str(e)
