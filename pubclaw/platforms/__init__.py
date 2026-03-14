"""
平台适配器注册中心
"""

from .base import BasePlatformAdapter
from .wechat import WechatAdapter

# 注册所有平台适配器
PLATFORM_ADAPTERS = {
    'wechat': WechatAdapter,
    'weixin': WechatAdapter,  # 别名
}


def get_adapter(platform: str) -> BasePlatformAdapter:
    """
    获取平台适配器实例
    
    Args:
        platform: 平台名称
        
    Returns:
        适配器实例
    """
    adapter_class = PLATFORM_ADAPTERS.get(platform.lower())
    if adapter_class:
        return adapter_class()
    return None


def list_supported_platforms() -> list:
    """
    获取支持的平台列表
    
    Returns:
        平台名称列表
    """
    return list(PLATFORM_ADAPTERS.keys())


def register_adapter(name: str, adapter_class):
    """
    注册新的平台适配器
    
    Args:
        name: 平台名称
        adapter_class: 适配器类
    """
    PLATFORM_ADAPTERS[name.lower()] = adapter_class
