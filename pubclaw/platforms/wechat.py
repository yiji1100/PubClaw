import requests
import json
import markdown
import re
import os
import hashlib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import html

class WechatAdapter:
    """
    微信公众号适配器 - 内容标准化管道实现
    参考架构：公众号内容标准化管道
    """
    name = 'wechat'
    
    # 图片缓存目录
    CACHE_DIR = os.path.expanduser('~/.pubclaw/cache/images')
    
    def __init__(self):
        self.access_token = None
        self.image_media_map = {}  # URL -> media_id 映射缓存
        os.makedirs(self.CACHE_DIR, exist_ok=True)
    
    def authenticate(self, credentials):
        """获取 access_token"""
        url = 'https://api.weixin.qq.com/cgi-bin/token'
        params = {
            'grant_type': 'client_credential',
            'appid': credentials.get('app_id'),
            'secret': credentials.get('app_secret')
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if 'access_token' in data:
                self.access_token = data['access_token']
                return True
        except Exception as e:
            print(f"认证失败: {e}")
        return False
    
    def clean_html(self, html_content):
        """
        第一步：统一输入与清洗
        剥离所有公众号不支持的标签和样式
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 移除不支持的标签
        for tag in soup.find_all(['script', 'style', 'iframe', 'video', 'audio']):
            tag.decompose()
        
        # 移除所有 class 和 style 属性
        for tag in soup.find_all():
            tag.attrs = {k: v for k, v in tag.attrs.items() 
                        if k in ['src', 'href', 'alt', 'title']}
        
        # 将 div 转换为 section（公众号更支持）
        for div in soup.find_all('div'):
            div.name = 'section'
        
        return str(soup)
    
    def upload_image(self, image_url, account_credentials):
        """
        第三步：图片资源处理
        下载图片并上传到公众号获取 media_id
        """
        # 检查缓存
        if image_url in self.image_media_map:
            return self.image_media_map[image_url]
        
        # 生成缓存文件名
        url_hash = hashlib.md5(image_url.encode()).hexdigest()
        ext = os.path.splitext(urlparse(image_url).path)[1] or '.jpg'
        cache_file = os.path.join(self.CACHE_DIR, f"{url_hash}{ext}")
        
        try:
            # 1. 下载图片
            if not os.path.exists(cache_file):
                resp = requests.get(image_url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                if resp.status_code == 200:
                    with open(cache_file, 'wb') as f:
                        f.write(resp.content)
                else:
                    return None
            
            # 2. 上传到公众号
            upload_url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={self.access_token}"
            
            with open(cache_file, 'rb') as f:
                files = {'media': f}
                resp = requests.post(upload_url, files=files, timeout=30)
            
            result = resp.json()
            
            if 'url' in result:
                # 临时素材返回 url
                self.image_media_map[image_url] = result['url']
                return result['url']
            
        except Exception as e:
            print(f"图片上传失败 {image_url}: {e}")
        
        return None
    
    def process_images(self, html_content, account_credentials):
        """
        处理 HTML 中的所有图片
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and src.startswith('http'):
                # 上传图片并获取新 URL
                new_url = self.upload_image(src, account_credentials)
                if new_url:
                    img['src'] = new_url
                else:
                    # 上传失败，保留原链接（可能被过滤）
                    pass
        
        return str(soup)
    
    def convert_markdown_to_wechat(self, md_content):
        """
        第二步：专用转换器
        将 Markdown 转换为公众号优化的 HTML
        """
        # 先转换为标准 HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code'],
            output_format='html5'
        )
        
        # 清洗 HTML
        html_content = self.clean_html(html_content)
        
        # 进一步优化公众号格式
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 为代码块添加公众号样式
        for pre in soup.find_all('pre'):
            pre['style'] = 'background:#f6f6f6;padding:10px;border-radius:4px;overflow-x:auto;'
        
        # 为引用块添加样式
        for blockquote in soup.find_all('blockquote'):
            blockquote['style'] = 'border-left:3px solid #07c160;padding-left:10px;margin:10px 0;color:#666;'
        
        return str(soup)
    
    def create_article(self, title, body, account_credentials, cover_image=None):
        """
        第四步：组装与API调用
        """
        # 1. 转换内容
        html_content = self.convert_markdown_to_wechat(body)
        
        # 2. 处理图片
        html_content = self.process_images(html_content, account_credentials)
        
        # 3. 组装文章
        article = {
            'title': title[:64],
            'content': html_content,
            'author': '小洛',
            'need_open_comment': 1,
            'only_fans_can_comment': 0
        }
        
        # 4. 添加封面图
        thumb_id = account_credentials.get('default_thumb_media_id')
        if thumb_id:
            article['thumb_media_id'] = thumb_id
        
        return article
    
    def publish(self, account, content, draft=True):
        """
        发布到公众号
        最佳实践：优先使用草稿箱接口
        """
        if not self.access_token:
            if not self.authenticate(account['credentials']):
                return {'success': False, 'error': '认证失败'}
        
        try:
            # 创建文章
            article = self.create_article(
                content.get('title', '无标题'),
                content.get('body', ''),
                account['credentials'],
                content.get('cover_image')
            )
            
            # 添加到草稿箱
            url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"
            
            data = {'articles': [article]}
            
            # 添加摘要
            digest = content.get('digest', '')
            if digest:
                article['digest'] = digest[:120]
            
            json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            
            resp = requests.post(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json; charset=utf-8'},
                timeout=30
            )

            # ⚠️ 注意：必须用 data=json_data，不能用 json=参数
            # requests.post(json=...) 会对中文进行 Unicode 转义 (\u8fd9...)
            # 而 data= 已预先用 ensure_ascii=False 编码为 UTF-8，可正确传输中文
            
            result = resp.json()
            
            if 'media_id' in result:
                return {
                    'success': True,
                    'media_id': result['media_id'],
                    'draft': True,
                    'message': '文章已创建为草稿，请登录公众号后台发布',
                    'image_count': len(self.image_media_map)
                }
            else:
                return {'success': False, 'error': result.get('errmsg', '未知错误')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_image_cache_stats(self):
        """获取图片缓存统计"""
        return {
            'cached_images': len(os.listdir(self.CACHE_DIR)),
            'media_map_entries': len(self.image_media_map)
        }
