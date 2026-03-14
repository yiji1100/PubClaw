import requests
import json
import markdown
import re
import os
import hashlib
import tempfile
from urllib.parse import urlparse
from bs4 import BeautifulSoup

class WechatAdapter:
    """
    微信公众号适配器 - 混合模式（首图+正文图片+底部文字）
    """
    name = 'wechat'
    
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
    
    def extract_sections(self, md_content):
        """
        将 Markdown 内容分割为三部分：
        1. 头部（首图）
        2. 正文（需要转为图片的部分）
        3. 底部（延伸阅读等文字内容）
        """
        lines = md_content.split('\n')
        
        # 找到 "延伸阅读" 或 "## 延伸阅读" 的位置
        related_reading_idx = -1
        for i, line in enumerate(lines):
            if '延伸阅读' in line or line.strip() == '## 延伸阅读':
                related_reading_idx = i
                break
        
        # 找到第一个空行后的内容（通常是导语）
        first_empty_line = -1
        for i, line in enumerate(lines):
            if i > 0 and line.strip() == '' and lines[i-1].strip().startswith('**导语**'):
                first_empty_line = i
                break
        
        if related_reading_idx == -1:
            # 没有找到延伸阅读，全部作为正文
            return '', md_content, ''
        
        # 分割内容
        header = '\n'.join(lines[:related_reading_idx])
        footer = '\n'.join(lines[related_reading_idx:])
        
        return header, '', footer  # 简化处理，先不分离导语
    
    def generate_header_html(self, title, cover_image=None, intro=''):
        """生成头部 HTML（导语部分）"""
        html_parts = []
        
        # 首图
        if cover_image:
            html_parts.append(f'<p><img src="{cover_image}" style="width:100%;margin:0;"></p>')
        
        # 标题
        html_parts.append(f'<h1 style="font-size:22px;font-weight:bold;margin:20px 0;border-bottom:2px solid #07c160;padding-bottom:10px;">{title}</h1>')
        
        # 导语
        if intro:
            html_parts.append(f'<p style="background:#f8f8f8;padding:15px;border-radius:5px;color:#555;"><strong>导语</strong>：{intro}</p>')
        
        return '\n'.join(html_parts)
    
    def generate_footer_html(self, related_links, qrcode_url=None):
        """生成底部 HTML（延伸阅读、二维码等）"""
        html_parts = []
        
        # 延伸阅读标题
        html_parts.append('<h2 style="font-size:18px;font-weight:bold;margin:25px 0 15px;padding-left:10px;border-left:4px solid #07c160;">延伸阅读</h2>')
        
        # 链接列表
        html_parts.append('<p>如果你对这个话题感兴趣，还可以阅读以下文章：</p>')
        html_parts.append('<ul style="margin:15px 0;padding-left:25px;">')
        for link_text, link_url in related_links:
            html_parts.append(f'<li style="margin:8px 0;"><a href="{link_url}" style="color:#07c160;text-decoration:none;">{link_text}</a></li>')
        html_parts.append('</ul>')
        
        # 互动话题
        html_parts.append('<h2 style="font-size:18px;font-weight:bold;margin:25px 0 15px;padding-left:10px;border-left:4px solid #07c160;">互动话题</h2>')
        html_parts.append('<p>你持有LOF基金吗？是通过场内还是场外持有的？欢迎在评论区分享你的经验！</p>')
        
        # 免责声明
        html_parts.append('<hr style="border:none;border-top:1px solid #e0e0e0;margin:30px 0;">')
        html_parts.append('<p style="font-size:13px;color:#999;"><em>免责声明：本文仅供学习交流，不构成投资建议。基金投资有风险，入市需谨慎。</em></p>')
        
        # 二维码
        if qrcode_url:
            html_parts.append('<div style="text-align:center;padding:25px;background:#f5f5f5;margin:25px 0;border-radius:5px;">')
            html_parts.append('<h3 style="margin:0 0 15px;color:#07c160;">加入交流群</h3>')
            html_parts.append(f'<p><img src="{qrcode_url}" style="max-width:150px;margin:10px auto;"></p>')
            html_parts.append('<p style="font-size:13px;color:#666;margin:10px 0 0;">扫码备注"LOF"，即可通过好友申请！</p>')
            html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    def markdown_to_body_html(self, body_md):
        """将正文 Markdown 转换为适合转图片的 HTML"""
        css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 16px;
            line-height: 1.8;
            color: #333;
            padding: 30px 25px;
            background: #fff;
            max-width: 700px;
            margin: 0 auto;
        }
        h2 {
            font-size: 19px;
            font-weight: 700;
            color: #1a1a1a;
            margin: 28px 0 16px;
            padding: 10px 0 10px 14px;
            border-left: 4px solid #07c160;
            background: linear-gradient(90deg, #f0f9f0 0%, transparent 100%);
        }
        h3 {
            font-size: 17px;
            font-weight: 700;
            color: #333;
            margin: 22px 0 12px;
        }
        h4 {
            font-size: 16px;
            font-weight: 700;
            color: #444;
            margin: 18px 0 10px;
        }
        p {
            margin: 14px 0;
            line-height: 1.8;
            text-align: justify;
        }
        ul, ol {
            margin: 14px 0;
            padding-left: 28px;
        }
        li {
            margin: 8px 0;
            line-height: 1.8;
        }
        blockquote {
            margin: 18px 0;
            padding: 14px 18px;
            background: #f8f8f8;
            border-left: 4px solid #07c160;
            color: #555;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 18px 0;
            font-size: 14px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px 12px;
            text-align: left;
        }
        th {
            background: #f5f5f5;
            font-weight: 700;
        }
        code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 14px;
            color: #e83e8c;
        }
        pre {
            background: #263238;
            color: #aed581;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 14px;
            line-height: 1.6;
            margin: 18px 0;
        }
        strong {
            color: #07c160;
            font-weight: 700;
        }
        hr {
            border: none;
            border-top: 1px solid #e0e0e0;
            margin: 28px 0;
        }
        </style>
        """
        
        # 转换 Markdown
        html_content = markdown.markdown(
            body_md,
            extensions=['tables', 'fenced_code'],
            output_format='html5'
        )
        
        return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{css}</head><body>{html_content}</body></html>"
    
    def html_to_image(self, html_content, output_path):
        """HTML 转图片并压缩"""
        try:
            from PIL import Image
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                html_path = f.name
            
            png_path = output_path.replace('.jpg', '.png')
            cmd = f"wkhtmltoimage --width 700 --quality 90 --enable-local-file-access {html_path} {png_path}"
            result = os.system(cmd)
            os.unlink(html_path)
            
            if result == 0 and os.path.exists(png_path):
                img = Image.open(png_path)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                img.save(output_path, 'JPEG', quality=85, optimize=True)
                os.unlink(png_path)
                return True
            return False
        except Exception as e:
            print(f"HTML转图片失败: {e}")
            return False
    
    def upload_image(self, image_path):
        """上传图片到微信"""
        if not self.access_token:
            return None
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={self.access_token}"
            with open(image_path, 'rb') as f:
                files = {'media': f}
                resp = requests.post(url, files=files, timeout=60)
            result = resp.json()
            return result.get('url')
        except Exception as e:
            print(f"上传失败: {e}")
            return None
    
    def publish_hybrid(self, account, content):
        """
        混合模式发布：
        - 头部：首图 + 导语（文字）
        - 中部：正文（转为图片）
        - 底部：延伸阅读 + 二维码（文字）
        """
        if not self.access_token:
            if not self.authenticate(account['credentials']):
                return {'success': False, 'error': '认证失败'}
        
        try:
            title = content.get('title', '无标题')[:64]
            full_body = content.get('body', '')
            cover_image = content.get('cover_image', '')
            
            # 提取各部分
            # 简化处理：正文到"## 延伸阅读"之前，之后是底部
            parts = full_body.split('## 延伸阅读')
            if len(parts) >= 2:
                body_part = parts[0].strip()
                footer_part = parts[1].strip()
            else:
                body_part = full_body
                footer_part = ''
            
            # 提取导语（假设在第一段）
            intro = ''
            if '**导语**：' in body_part:
                intro_match = re.search(r'\*\*导语\*\*：(.+?)(?=\n\n|\Z)', body_part, re.DOTALL)
                if intro_match:
                    intro = intro_match.group(1).strip()
                    # 从正文中移除导语
                    body_part = re.sub(r'\*\*导语\*\*：.+?(?=\n\n|\Z)', '', body_part, count=1, flags=re.DOTALL).strip()
            
            # 1. 生成头部 HTML
            header_html = self.generate_header_html(title, cover_image, intro)
            
            # 2. 生成正文图片
            content_hash = hashlib.md5(body_part.encode()).hexdigest()[:8]
            image_path = os.path.join(self.IMAGE_CACHE_DIR, f"body_{content_hash}.jpg")
            
            if not os.path.exists(image_path):
                body_html = self.markdown_to_body_html(body_part)
                success = self.html_to_image(body_html, image_path)
                if not success:
                    return {'success': False, 'error': '正文图片生成失败'}
            
            body_image_url = self.upload_image(image_path)
            if not body_image_url:
                return {'success': False, 'error': '正文图片上传失败'}
            
            # 3. 生成底部 HTML（解析延伸阅读）
            footer_html = ''
            if footer_part:
                # 解析链接
                links = re.findall(r'- \[(.+?)\]\((.+?)\)', footer_part)
                
                # 提取二维码图片
                qrcode_match = re.search(r'!\[.*?\]\((https?://[^\)]+)\)', footer_part)
                qrcode_url = qrcode_match.group(1) if qrcode_match else None
                
                footer_html = self.generate_footer_html(links, qrcode_url)
            
            # 4. 组装完整内容
            full_html = f"""
            {header_html}
            <p style="margin:20px 0;"><img src="{body_image_url}" style="width:100%;display:block;"></p>
            {footer_html}
            """
            
            # 5. 发布
            article = {
                'title': title,
                'content': full_html,
                'author': content.get('author', '小洛')[:8],
                'need_open_comment': 1,
                'only_fans_can_comment': 0
            }
            
            thumb_id = account['credentials'].get('default_thumb_media_id')
            if thumb_id:
                article['thumb_media_id'] = thumb_id
            
            digest = content.get('digest', '')
            if digest:
                article['digest'] = digest[:120]
            
            url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"
            data = {'articles': [article]}
            
            json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            resp = requests.post(url, data=json_data, headers={'Content-Type': 'application/json; charset=utf-8'}, timeout=30)
            result = resp.json()
            
            if 'media_id' in result:
                return {
                    'success': True,
                    'media_id': result['media_id'],
                    'draft': True,
                    'mode': 'hybrid',
                    'message': '混合模式发布成功（首图+正文图片+底部文字）'
                }
            else:
                return {'success': False, 'error': result.get('errmsg', '未知错误')}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def publish(self, account, content, draft=True, mode='hybrid'):
        """
        发布内容
        mode: 'hybrid' - 混合模式（推荐）
              'image' - 全图片模式
              'text' - 纯文本模式
        """
        if mode == 'hybrid':
            return self.publish_hybrid(account, content)
        elif mode == 'image':
            # 导入图片模式适配器
            from .wechat_image import WechatAdapter as ImageAdapter
            adapter = ImageAdapter()
            adapter.access_token = self.access_token
            return adapter.publish_as_image(account, content)
        else:
            return {'success': False, 'error': '不支持的模式'}
