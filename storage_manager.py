import json
import os
import uuid
from datetime import datetime
from cryptography.fernet import Fernet


class StorageManager:
    """存储管理器类"""

    def __init__(self, data_file="accounts.dat", key_file=".key"):
        self.data_file = data_file
        self.key_file = key_file
        self.cipher = None

        # 初始化加密
        self._init_encryption()

        # 确保数据文件存在
        if not os.path.exists(self.data_file):
            self._save_data({"accounts": []})

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
