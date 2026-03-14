#!/usr/bin/env python3
"""
账号管理服务 - AccountManager
负责多平台账号的增删改查和安全管理
"""

import json
import os
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class AccountManager:
    """账号管理器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.data_dir = os.path.expanduser("~/.pubclaw")
        self.accounts_file = os.path.join(self.data_dir, "accounts.json")
        
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化加密
        self._init_crypto()
        
        # 加载账号
        self.accounts: Dict[str, List[Dict]] = self._load_accounts()
    
    def _init_crypto(self):
        """初始化加密"""
        # 从环境变量或配置文件获取密钥
        key_base = os.getenv('PUBCLAW_SECRET_KEY', 'default-key-change-it')
        
        # 使用PBKDF2派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'pubclaw-salt-v1',
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key_base.encode()))
        self.cipher = Fernet(key)
    
    def _load_accounts(self) -> Dict[str, List[Dict]]:
        """加载账号数据"""
        if not os.path.exists(self.accounts_file):
            return {}
        
        try:
            with open(self.accounts_file, 'r') as f:
                data = json.load(f)
                # 解密凭证
                for platform, accounts in data.items():
                    for acc in accounts:
                        if 'credentials_encrypted' in acc:
                            acc['credentials'] = self._decrypt(acc['credentials_encrypted'])
                            del acc['credentials_encrypted']
                return data
        except Exception as e:
            logger.error(f"加载账号失败: {e}")
            return {}
    
    def _save_accounts(self):
        """保存账号数据"""
        try:
            # 加密凭证
            data_to_save = {}
            for platform, accounts in self.accounts.items():
                data_to_save[platform] = []
                for acc in accounts:
                    acc_copy = acc.copy()
                    if 'credentials' in acc_copy:
                        acc_copy['credentials_encrypted'] = self._encrypt(acc_copy['credentials'])
                        del acc_copy['credentials']
                    data_to_save[platform].append(acc_copy)
            
            with open(self.accounts_file, 'w') as f:
                json.dump(data_to_save, f, indent=2)
                
            # 设置文件权限（仅所有者读写）
            os.chmod(self.accounts_file, 0o600)
            
        except Exception as e:
            logger.error(f"保存账号失败: {e}")
            raise
    
    def _encrypt(self, data: Dict) -> str:
        """加密数据"""
        json_str = json.dumps(data)
        encrypted = self.cipher.encrypt(json_str.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def _decrypt(self, encrypted_str: str) -> Dict:
        """解密数据"""
        encrypted = base64.urlsafe_b64decode(encrypted_str.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
    
    async def add_account(
        self,
        platform: str,
        account_id: str,
        credentials: Dict,
        account_type: str = "personal",
        group: str = "default"
    ) -> bool:
        """
        添加账号
        """
        try:
            account = {
                'account_id': account_id,
                'platform': platform,
                'account_type': account_type,
                'group': group,
                'credentials': credentials,
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'last_used': None,
                'publish_count': 0,
                'error_count': 0
            }
            
            if platform not in self.accounts:
                self.accounts[platform] = []
            
            # 检查是否已存在
            existing = [a for a in self.accounts[platform] if a['account_id'] == account_id]
            if existing:
                # 更新现有账号
                idx = self.accounts[platform].index(existing[0])
                self.accounts[platform][idx] = account
                logger.info(f"更新账号: {platform}/{account_id}")
            else:
                self.accounts[platform].append(account)
                logger.info(f"添加账号: {platform}/{account_id}")
            
            self._save_accounts()
            return True
            
        except Exception as e:
            logger.error(f"添加账号失败: {e}")
            return False
    
    async def get_active_account(self, platform: str) -> Optional[Dict]:
        """
        获取可用账号（自动续签）
        """
        if platform not in self.accounts:
            return None
        
        # 过滤可用账号
        active_accounts = [
            a for a in self.accounts[platform]
            if a['status'] in ['active', 'token_expired']
        ]
        
        if not active_accounts:
            return None
        
        # 按优先级选择（最少使用、最近未报错）
        active_accounts.sort(key=lambda x: (x['error_count'], x['publish_count']))
        
        selected = active_accounts[0]
        
        # 检查token是否过期
        creds = selected['credentials']
        expires_at = creds.get('expires_at')
        
        if expires_at:
            expires_time = datetime.fromtimestamp(expires_at)
            if datetime.now() > expires_time - timedelta(minutes=10):
                # 需要续签
                logger.info(f"账号token即将过期，尝试续签: {selected['account_id']}")
                # 这里调用平台的续签逻辑
                # await self._refresh_token(platform, selected)
        
        # 更新使用时间
        selected['last_used'] = datetime.now().isoformat()
        self._save_accounts()
        
        return selected
    
    async def list_accounts(self, platform: Optional[str] = None) -> List[Dict]:
        """
        列出账号
        """
        if platform:
            return self.accounts.get(platform, [])
        
        # 返回所有账号
        all_accounts = []
        for plat, accounts in self.accounts.items():
            for acc in accounts:
                all_accounts.append({
                    'platform': plat,
                    'account_id': acc['account_id'],
                    'account_type': acc['account_type'],
                    'group': acc['group'],
                    'status': acc['status'],
                    'publish_count': acc['publish_count'],
                    'last_used': acc['last_used']
                })
        
        return all_accounts
    
    async def update_account_status(
        self,
        platform: str,
        account_id: str,
        status: str,
        error: Optional[str] = None
    ):
        """
        更新账号状态
        """
        if platform not in self.accounts:
            return
        
        for acc in self.accounts[platform]:
            if acc['account_id'] == account_id:
                acc['status'] = status
                
                if status == 'active':
                    acc['error_count'] = 0
                elif status == 'error':
                    acc['error_count'] = acc.get('error_count', 0) + 1
                    
                    # 错误次数过多，标记为禁用
                    if acc['error_count'] >= 5:
                        acc['status'] = 'disabled'
                        logger.warning(f"账号错误过多已禁用: {platform}/{account_id}")
                
                self._save_accounts()
                break
    
    async def record_publish(self, platform: str, account_id: str, success: bool):
        """
        记录发布结果
        """
        if platform not in self.accounts:
            return
        
        for acc in self.accounts[platform]:
            if acc['account_id'] == account_id:
                acc['publish_count'] = acc.get('publish_count', 0) + 1
                if not success:
                    acc['error_count'] = acc.get('error_count', 0) + 1
                self._save_accounts()
                break
    
    async def delete_account(self, platform: str, account_id: str) -> bool:
        """
        删除账号
        """
        if platform not in self.accounts:
            return False
        
        original_count = len(self.accounts[platform])
        self.accounts[platform] = [
            a for a in self.accounts[platform]
            if a['account_id'] != account_id
        ]
        
        if len(self.accounts[platform]) < original_count:
            self._save_accounts()
            logger.info(f"删除账号: {platform}/{account_id}")
            return True
        
        return False
    
    async def add_account_interactive(self, platform: str):
        """
        交互式添加账号（命令行使用）
        """
        print(f"\n添加 {platform} 账号")
        print("-" * 40)
        
        account_id = input("账号ID (唯一标识): ").strip()
        account_type = input("账号类型 (personal/business) [personal]: ").strip() or "personal"
        group = input("分组 [default]: ").strip() or "default"
        
        # 根据平台提示输入凭证
        credentials = {}
        
        if platform == "wechat":
            credentials['app_id'] = input("AppID: ").strip()
            credentials['app_secret'] = input("AppSecret: ").strip()
            thumb_id = input("封面图MediaID (可选): ").strip()
            if thumb_id:
                credentials['default_thumb_media_id'] = thumb_id
        
        # 可以扩展其他平台的输入逻辑
        
        success = await self.add_account(
            platform=platform,
            account_id=account_id,
            credentials=credentials,
            account_type=account_type,
            group=group
        )
        
        if success:
            print(f"✅ 账号添加成功: {account_id}")
        else:
            print(f"❌ 账号添加失败")
