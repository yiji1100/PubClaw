#!/usr/bin/env python3
"""
微信公众号平台适配器
支持图文发布、草稿管理
"""

import requests
import json
import re
import markdown
from typing import Dict, Optional, Any
import logging

from .base import BasePlatformAdapter

logger = logging.getLogger(__name__)


class WechatAdapter(BasePlatformAdapter):
    """微信公众号适配器"""
    
    name = "wechat"
    display_name = "微信公众号"
    
    # 接口限制
    RATE_LIMIT = 5  # 每分钟最多5次
    
    # 内容限制
    CONTENT_LIMITS = {
        'title_max': 64,
        'author_max': 8,
        'digest_max': 120,
        'content_max': 20000,
        'image_max_size': 10 * 1024 * 1024,  # 10MB
    }
    
    def __init__(self):
        self.access_token: Optional[str] = None
        self.token_expires: Optional[int] = None
    
    async def authenticate(self, credentials: Dict) -> bool:
        """
        认证并获取access_token
        """
        try:
            app_id = credentials.get('app_id')
            app_secret = credentials.get('app_secret')
            
            if not app_id or not app_secret:
                logger.error("缺少AppID或AppSecret")
                return False
            
            url = "https://api.weixin.qq.com/cgi-bin/token"
            params = {
                'grant_type': 'client_credential',
                'appid': app_id,
                'secret': app_secret
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'access_token' in data:
                self.access_token = data['access_token']
                self.token_expires = data.get('expires_in', 7200)
                logger.info("微信公众号认证成功")
                return True
            else:
                logger.error(f"认证失败: {data}")
                return False
                
        except Exception as e:
            logger.error(f"认证异常: {e}")
            return False
    
    async def publish(
        self,
        account: Dict,
        content: Dict,
        draft: bool = True,
        options: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发布内容
        """
        try:
            # 确保已认证
            if not self.access_token:
                success = await self.authenticate(account['credentials'])
                if not success:
                    return {'success': False, 'error': '认证失败'}
            
            # 准备文章内容
            article = await self._prepare_article(content)
            
            # 创建草稿
            draft_result = await self._create_draft(article)
            
            if not draft_result.get('success'):
                return draft_result
            
            media_id = draft_result['media_id']
            
            # 如果不只是草稿，则发布
            if not draft:
                publish_result = await self._publish_draft(media_id)
                return publish_result
            
            return {
                'success': True,
                'media_id': media_id,
                'message': '草稿创建成功，请登录公众号后台确认发布',
                'draft': True
            }
            
        except Exception as e:
            logger.error(f"发布失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _prepare_article(self, content: Dict) -> Dict:
        """
        准备文章数据
        """
        title = content.get('title', '')
        body = content.get('body', '')
        author = content.get('author', '小洛')
        cover_url = content.get('cover_url', '')
        
        # 检查标题长度
        if len(title) > self.CONTENT_LIMITS['title_max']:
            title = title[:self.CONTENT_LIMITS['title_max'] - 3] + '...'
        
        # Markdown转HTML
        html_content = self._markdown_to_wechat_html(body)
        
        # 处理封面图
        thumb_media_id = content.get('thumb_media_id', '')
        
        article = {
            'title': title,
            'author': author[:self.CONTENT_LIMITS['author_max']],
            'content': html_content,
            'content_source_url': content.get('source_url', ''),
            'need_open_comment': 1,
            'only_fans_can_comment': 0
        }
        
        if thumb_media_id:
            article['thumb_media_id'] = thumb_media_id
        
        return article
    
    def _markdown_to_wechat_html(self, md_content: str) -> str:
        """
        Markdown转微信公众号HTML
        """
        # 基础转换
        html = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code', 'nl2br']
        )
        
        # 添加公众号样式
        styled_html = f"""
        <html>
        <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 16px; line-height: 1.8; color: #333; max-width: 100%; margin: 0; padding: 16px; }}
        h1 {{ font-size: 22px; font-weight: bold; color: #1a1a1a; margin: 24px 0 16px; padding-bottom: 8px; border-bottom: 2px solid #e0e0e0; }}
        h2 {{ font-size: 18px; font-weight: bold; color: #2c2c2c; margin: 20px 0 12px; }}
        h3 {{ font-size: 16px; font-weight: bold; color: #444; margin: 16px 0 8px; }}
        p {{ margin: 12px 0; text-align: justify; }}
        table {{ border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }}
        th, td {{ border: 1px solid #e0e0e0; padding: 10px; text-align: left; }}
        th {{ background-color: #f5f5f5; font-weight: bold; }}
        blockquote {{ border-left: 4px solid #07c160; background-color: #f0f9f0; padding: 12px 16px; margin: 16px 0; color: #666; }}
        code {{ background-color: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 14px; }}
        pre {{ background-color: #f8f8f8; padding: 12px; border-radius: 6px; overflow-x: auto; }}
        img {{ max-width: 100%; height: auto; display: block; margin: 16px auto; }}
        strong {{ color: #07c160; }}
        ul, ol {{ margin: 12px 0; padding-left: 24px; }}
        li {{ margin: 6px 0; }}
        </style>
        </head>
        <body>{html}</body>
        </html>
        """
        
        return styled_html.strip()
    
    async def _create_draft(self, article: Dict) -> Dict:
        """
        创建草稿
        """
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"
        
        data = {
            'articles': [article]
        }
        
        response = requests.post(
            url,
            data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        result = response.json()
        
        if 'media_id' in result:
            logger.info(f"草稿创建成功: {result['media_id']}")
            return {
                'success': True,
                'media_id': result['media_id']
            }
        else:
            logger.error(f"创建草稿失败: {result}")
            return {
                'success': False,
                'error': result.get('errmsg', '未知错误'),
                'errcode': result.get('errcode', -1)
            }
    
    async def _publish_draft(self, media_id: str) -> Dict:
        """
        发布草稿
        """
        url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={self.access_token}"
        
        data = {'media_id': media_id}
        
        response = requests.post(
            url,
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        result = response.json()
        
        if result.get('errcode') == 0:
            logger.info(f"发布成功: {result.get('publish_id')}")
            return {
                'success': True,
                'publish_id': result.get('publish_id'),
                'msg_data_id': result.get('msg_data_id')
            }
        else:
            logger.error(f"发布失败: {result}")
            return {
                'success': False,
                'error': result.get('errmsg', '未知错误'),
                'errcode': result.get('errcode')
            }
    
    async def upload_image(self, image_path: str) -> Optional[str]:
        """
        上传图片获取URL
        """
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={self.access_token}"
            
            with open(image_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, files=files, timeout=30)
            
            result = response.json()
            
            if 'url' in result:
                return result['url']
            else:
                logger.error(f"上传图片失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"上传图片异常: {e}")
            return None
    
    def get_rate_limit(self) -> int:
        """获取频率限制"""
        return self.RATE_LIMIT
