#!/usr/bin/env python3
"""
平台适配器基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class BasePlatformAdapter(ABC):
    """平台适配器基类"""
    
    name: str = ""
    display_name: str = ""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict) -> bool:
        """
        认证并初始化
        
        Args:
            credentials: 账号凭证
            
        Returns:
            是否认证成功
        """
        pass
    
    @abstractmethod
    async def publish(
        self,
        account: Dict,
        content: Dict,
        draft: bool = True,
        options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发布内容
        
        Args:
            account: 账号信息
            content: 内容数据
            draft: 是否创建草稿
            options: 额外选项
            
        Returns:
            发布结果
        """
        pass
    
    def get_rate_limit(self) -> int:
        """
        获取频率限制（每分钟请求数）
        
        Returns:
            频率限制数值
        """
        return 5  # 默认5次/分钟
    
    async def check_status(self, post_id: str) -> Dict:
        """
        检查发布状态（可选实现）
        
        Args:
            post_id: 发布ID
            
        Returns:
            状态信息
        """
        return {'status': 'unknown'}
    
    async def delete_post(self, post_id: str) -> bool:
        """
        删除内容（可选实现）
        
        Args:
            post_id: 发布ID
            
        Returns:
            是否删除成功
        """
        return False
