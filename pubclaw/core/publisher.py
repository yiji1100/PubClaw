#!/usr/bin/env python3
"""
发布执行服务 - Publisher
负责协调各平台发布流程
"""

import asyncio
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from ..platforms import get_adapter
from .account_mgr import AccountManager
from .content_adapter import ContentAdapter
from .monitor import Monitor

logger = logging.getLogger(__name__)


class Publisher:
    """发布执行器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.account_mgr = AccountManager(config_path)
        self.content_adapter = ContentAdapter()
        self.monitor = Monitor()
        self.tasks: Dict[str, Dict] = {}  # 任务存储
        
        # 并发控制（令牌桶）
        self.semaphores: Dict[str, asyncio.Semaphore] = {}
        
    async def publish(
        self, 
        platform: str, 
        content: str,
        title: Optional[str] = None,
        cover: Optional[str] = None,
        draft: bool = True,
        options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发布内容到指定平台
        
        Args:
            platform: 平台名称
            content: 内容（Markdown格式）
            title: 标题（可选）
            cover: 封面图路径（可选）
            draft: 是否创建草稿
            options: 额外选项
            
        Returns:
            发布结果
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"
        
        try:
            # 1. 创建任务记录
            self.tasks[task_id] = {
                'id': task_id,
                'platform': platform,
                'status': 'processing',
                'created_at': datetime.now().isoformat(),
                'content_preview': content[:100] + '...' if len(content) > 100 else content
            }
            
            # 2. 获取平台适配器
            adapter = get_adapter(platform)
            if not adapter:
                raise ValueError(f"不支持的平台: {platform}")
            
            # 3. 获取账号
            account = await self.account_mgr.get_active_account(platform)
            if not account:
                raise Exception(f"没有可用的{platform}账号")
            
            # 4. 内容适配
            adapted_content = await self.content_adapter.adapt(
                platform=platform,
                content=content,
                title=title,
                cover=cover
            )
            
            # 5. 并发控制
            if platform not in self.semaphores:
                # 从配置读取并发限制，默认5
                limit = adapter.get_rate_limit()
                self.semaphores[platform] = asyncio.Semaphore(limit)
            
            async with self.semaphores[platform]:
                # 6. 执行发布（带重试）
                result = await self._publish_with_retry(
                    adapter=adapter,
                    account=account,
                    content=adapted_content,
                    draft=draft,
                    options=options
                )
            
            # 7. 更新任务状态
            self.tasks[task_id].update({
                'status': 'success' if result.get('success') else 'failed',
                'published_at': datetime.now().isoformat(),
                'platform_post_id': result.get('post_id'),
                'url': result.get('url'),
                'message': result.get('message')
            })
            
            # 8. 记录监控
            await self.monitor.record_publish(
                task_id=task_id,
                platform=platform,
                success=result.get('success', False),
                duration=result.get('duration', 0)
            )
            
            return {
                'success': result.get('success', False),
                'task_id': task_id,
                'post_id': result.get('post_id'),
                'url': result.get('url'),
                'message': result.get('message', '')
            }
            
        except Exception as e:
            logger.error(f"发布失败 [{task_id}]: {e}")
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            
            await self.monitor.record_error(
                task_id=task_id,
                platform=platform,
                error=str(e)
            )
            
            return {
                'success': False,
                'task_id': task_id,
                'error': str(e)
            }
    
    async def publish_multi(
        self,
        platforms: List[str],
        content: str,
        title: Optional[str] = None,
        cover: Optional[str] = None,
        draft: bool = True
    ) -> Dict[str, Dict]:
        """
        多平台同时发布
        """
        results = {}
        
        # 并发执行所有平台发布
        tasks = [
            self.publish(
                platform=p,
                content=content,
                title=title,
                cover=cover,
                draft=draft
            )
            for p in platforms
        ]
        
        platform_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for platform, result in zip(platforms, platform_results):
            if isinstance(result, Exception):
                results[platform] = {
                    'success': False,
                    'error': str(result)
                }
            else:
                results[platform] = result
        
        return results
    
    async def _publish_with_retry(
        self,
        adapter,
        account: Dict,
        content: Dict,
        draft: bool,
        options: Optional[Dict],
        max_retries: int = 3
    ) -> Dict:
        """
        带重试机制的发布
        """
        start_time = time.time()
        
        for attempt in range(max_retries):
            try:
                result = await adapter.publish(
                    account=account,
                    content=content,
                    draft=draft,
                    options=options
                )
                
                result['duration'] = time.time() - start_time
                return result
                
            except Exception as e:
                error_msg = str(e)
                
                # 判断是否需要重试
                if self._should_retry(error_msg) and attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 指数退避
                    logger.warning(f"发布失败，{wait_time}秒后重试 ({attempt+1}/{max_retries}): {error_msg}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
        
        return {'success': False, 'error': 'Max retries exceeded'}
    
    def _should_retry(self, error_msg: str) -> bool:
        """
        判断错误是否可重试
        """
        retryable_errors = [
            'network',
            'timeout',
            'connection',
            'rate limit',
            'temporarily unavailable',
            '502',
            '503',
            '504'
        ]
        
        error_lower = error_msg.lower()
        return any(err in error_lower for err in retryable_errors)
    
    async def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        return self.tasks.get(task_id, {'status': 'not_found'})
    
    async def get_stats(self) -> Dict:
        """获取统计信息"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        today_tasks = [
            t for t in self.tasks.values()
            if t['created_at'].startswith(today)
        ]
        
        success_count = sum(1 for t in today_tasks if t['status'] == 'success')
        total_count = len(today_tasks)
        
        return {
            'today_count': total_count,
            'today_success': success_count,
            'success_rate': success_count / total_count * 100 if total_count > 0 else 0,
            'queue_length': len([t for t in self.tasks.values() if t['status'] == 'processing']),
            'total_tasks': len(self.tasks)
        }
