import requests
import json
import markdown
import re
import os
import hashlib
import base64
import tempfile
from urllib.parse import urlparse

class WechatAdapter:
    """
    微信公众号适配器 - 支持图片模式发布
    """
    name = 'wechat'
    
    # 缓存目录
    CACHE_DIR = os.path.expanduser('~/.pubclaw/cache')
    IMAGE_CACHE_DIR = os.path.join(CACHE_DIR, 'images')
    
    def __init__(self):
        self.access_token = None
        self.image_media_map = {}
        os.makedirs(self.IMAGE_CACHE_DIR, exist_ok=True)
    
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
    
    def markdown_to_html(self, md_content, title=''):
        """
        将 Markdown 转换为适合渲染的 HTML
        """
        # 基础 CSS - 模仿 VSCode 预览风格
        css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            font-size: 16px;
            line-height: 1.8;
            color: #333;
            padding: 40px;
            background: #fff;
            max-width: 750px;
            margin: 0 auto;
        }
        
        h1 {
            font-size: 26px;
            font-weight: 700;
            color: #1a1a1a;
            margin: 0 0 24px 0;
            padding-bottom: 12px;
            border-bottom: 2px solid #07c160;
            line-height: 1.4;
        }
        
        h2 {
            font-size: 20px;
            font-weight: 700;
            color: #2c2c2c;
            margin: 32px 0 16px 0;
            padding: 10px 0 10px 14px;
            border-left: 4px solid #07c160;
            background: linear-gradient(90deg, #f0f9f0 0%, transparent 100%);
            line-height: 1.4;
        }
        
        h3 {
            font-size: 17px;
            font-weight: 700;
            color: #444;
            margin: 24px 0 12px 0;
            line-height: 1.4;
        }
        
        p {
            margin: 16px 0;
            line-height: 1.8;
            text-align: justify;
        }
        
        ul, ol {
            margin: 16px 0;
            padding-left: 28px;
        }
        
        li {
            margin: 8px 0;
            line-height: 1.8;
        }
        
        ul ul, ol ul {
            margin: 8px 0;
        }
        
        blockquote {
            margin: 20px 0;
            padding: 16px 20px;
            background: #f8f8f8;
            border-left: 4px solid #07c160;
            color: #555;
            font-style: italic;
        }
        
        blockquote p {
            margin: 8px 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        
        th {
            background: #f5f5f5;
            font-weight: 700;
        }
        
        tr:nth-child(even) {
            background: #fafafa;
        }
        
        code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 14px;
            color: #e83e8c;
        }
        
        pre {
            background: #263238;
            color: #aed581;
            padding: 16px;
            border-radius: 8px;
            overflow-x: auto;
            font-size: 14px;
            line-height: 1.6;
            margin: 20px 0;
        }
        
        pre code {
            background: transparent;
            color: inherit;
            padding: 0;
        }
        
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
        }
        
        hr {
            border: none;
            border-top: 1px solid #e0e0e0;
            margin: 32px 0;
        }
        
        a {
            color: #07c160;
            text-decoration: none;
        }
        
        strong {
            color: #07c160;
            font-weight: 700;
        }
        
        .cover-img {
            width: 100%;
            margin: 0 0 24px 0;
        }
        
        .intro {
            background: #f8f8f8;
            padding: 16px 20px;
            margin: 20px 0;
            border-radius: 8px;
            font-size: 15px;
            color: #555;
        }
        
        .section-title {
            font-weight: 700;
            color: #333;
            margin: 16px 0 8px 0;
        }
        </style>
        """
        
        # 转换 Markdown 为 HTML
        html_content = markdown.markdown(
            md_content,
            extensions=['tables', 'fenced_code'],
            output_format='html5'
        )
        
        # 组装完整 HTML
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{css}
</head>
<body>
{html_content}
</body>
</html>"""
        
        return full_html
    
    def html_to_image(self, html_content, output_path):
        """
        使用 wkhtmltoimage 将 HTML 转换为图片，并自动压缩
        """
        try:
            from PIL import Image
            
            # 保存 HTML 到临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                html_path = f.name
            
            # 使用 wkhtmltoimage 转换
            png_path = output_path.replace('.jpg', '.png')
            cmd = f"wkhtmltoimage --width 750 --quality 90 --enable-local-file-access {html_path} {png_path}"
            result = os.system(cmd)
            
            # 清理临时文件
            os.unlink(html_path)
            
            if result == 0 and os.path.exists(png_path):
                # 压缩图片
                img = Image.open(png_path)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                img.save(output_path, 'JPEG', quality=85, optimize=True)
                
                # 删除原始 PNG
                os.unlink(png_path)
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"HTML转图片失败: {e}")
            return False
    
    def upload_image_to_wechat(self, image_path):
        """
        上传图片到微信素材库
        """
        if not self.access_token:
            return None
        
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={self.access_token}"
            
            with open(image_path, 'rb') as f:
                files = {'media': f}
                resp = requests.post(url, files=files, timeout=30)
            
            result = resp.json()
            
            if 'url' in result:
                return result['url']
            else:
                print(f"上传失败: {result}")
                return None
                
        except Exception as e:
            print(f"上传异常: {e}")
            return None
    
    def publish_as_image(self, account, content):
        """
        将内容作为图片发布
        
        方案：
        1. Markdown -> HTML
        2. HTML -> 图片 (长图)
        3. 图片上传到微信素材库
        4. 创建只包含图片的图文消息
        """
        if not self.access_token:
            if not self.authenticate(account['credentials']):
                return {'success': False, 'error': '认证失败'}
        
        try:
            title = content.get('title', '无标题')[:64]
            body = content.get('body', '')
            
            # 1. 生成 HTML
            html_content = self.markdown_to_html(body, title)
            
            # 2. 生成图片路径（使用 jpg 格式）
            content_hash = hashlib.md5(body.encode()).hexdigest()[:8]
            image_path = os.path.join(self.IMAGE_CACHE_DIR, f"article_{content_hash}.jpg")
            
            # 3. 检查缓存
            if not os.path.exists(image_path):
                # 需要生成图片
                # 注意：这需要服务器安装 wkhtmltopdf
                success = self.html_to_image(html_content, image_path)
                if not success:
                    # 如果图片生成失败，回退到文本模式
                    return self.publish_as_text(account, content)
            
            # 4. 上传图片到微信
            image_url = self.upload_image_to_wechat(image_path)
            
            if not image_url:
                return {'success': False, 'error': '图片上传失败'}
            
            # 5. 创建图文消息（只包含图片）
            article_html = f'<p><img src="{image_url}" style="width:100%;"></p>'
            
            article = {
                'title': title,
                'content': article_html,
                'author': content.get('author', '小洛')[:8],
                'need_open_comment': 1,
                'only_fans_can_comment': 0
            }
            
            # 添加封面图
            thumb_id = account['credentials'].get('default_thumb_media_id')
            if thumb_id:
                article['thumb_media_id'] = thumb_id
            
            # 添加摘要
            digest = content.get('digest', '')
            if digest:
                article['digest'] = digest[:120]
            
            # 6. 发布到草稿箱
            url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"
            data = {'articles': [article]}
            
            json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            
            resp = requests.post(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json; charset=utf-8'},
                timeout=30
            )
            
            result = resp.json()
            
            if 'media_id' in result:
                return {
                    'success': True,
                    'media_id': result['media_id'],
                    'draft': True,
                    'mode': 'image',
                    'message': '文章已转为图片并创建为草稿，请登录公众号后台发布',
                    'image_path': image_path,
                    'image_url': image_url
                }
            else:
                return {'success': False, 'error': result.get('errmsg', '未知错误')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def publish_as_text(self, account, content):
        """
        传统文本模式发布（备用方案）
        """
        # ... 之前的文本发布逻辑
        pass
    
    def publish(self, account, content, draft=True, mode='auto'):
        """
        发布内容
        
        Args:
            mode: 'auto' - 自动选择最佳模式
                  'image' - 强制图片模式
                  'text' - 强制文本模式
        """
        if mode == 'image':
            return self.publish_as_image(account, content)
        elif mode == 'text':
            return self.publish_as_text(account, content)
        else:
            # 自动模式：优先尝试图片，失败则回退文本
            result = self.publish_as_image(account, content)
            if result.get('success'):
                return result
            else:
                print(f"图片模式失败，回退到文本模式: {result.get('error')}")
                return self.publish_as_text(account, content)
