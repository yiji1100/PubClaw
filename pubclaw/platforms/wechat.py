import requests
import json
import markdown
import re

class WechatAdapter:
    name = 'wechat'
    
    # 极简 CSS，让微信编辑器自动处理大部分样式
    WECHAT_CSS = """
    <style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
        font-size: 16px;
        line-height: 1.8;
        color: #333;
    }
    h1 {
        font-size: 22px;
        font-weight: bold;
        margin: 24px 0 16px;
        border-bottom: 2px solid #07c160;
        padding-bottom: 8px;
    }
    h2 {
        font-size: 18px;
        font-weight: bold;
        margin: 20px 0 12px;
        border-left: 4px solid #07c160;
        padding-left: 10px;
    }
    h3 {
        font-size: 16px;
        font-weight: bold;
        margin: 16px 0 10px;
    }
    p {
        margin: 12px 0;
        line-height: 1.8;
    }
    ul, ol {
        margin: 12px 0;
        padding-left: 24px;
    }
    li {
        margin: 8px 0;
        line-height: 1.8;
    }
    blockquote {
        margin: 16px 0;
        padding: 12px 16px;
        background: #f5f5f5;
        border-left: 4px solid #07c160;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 16px 0;
        font-size: 14px;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 10px;
        text-align: left;
    }
    th {
        background: #f5f5f5;
        font-weight: bold;
    }
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 16px auto;
    }
    a {
        color: #07c160;
        text-decoration: none;
    }
    hr {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 24px 0;
    }
    strong {
        color: #07c160;
        font-weight: bold;
    }
    </style>
    """
    
    def authenticate(self, credentials):
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
        except:
            pass
        return False
    
    def format_content(self, body):
        """
        将 Markdown 转换为简洁的 HTML
        """
        # 使用标准 markdown 转换
        html = markdown.markdown(
            body, 
            extensions=['tables', 'fenced_code'],
            output_format='html5'
        )
        
        # 清理多余的 br 标签
        html = re.sub(r'<br\s*/?>\s*<br\s*/?>', '</p><p>', html)
        html = re.sub(r'<br\s*/?>', '', html)
        
        # 处理 p 标签内的空行（合并相邻的 p 标签）
        html = re.sub(r'</p>\s*<p>\s*</p>', '</p>', html)
        
        return html
    
    def create_article_html(self, title, body, cover_image=None):
        """
        创建简洁的微信公众号文章HTML
        """
        content_html = self.format_content(body)
        
        # 添加首图
        cover_html = ''
        if cover_image:
            cover_html = f'<p><img src="{cover_image}" alt="封面"></p>'
        
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{self.WECHAT_CSS}
</head>
<body>
{cover_html}
{content_html}
</body>
</html>"""
        
        return full_html
    
    def publish(self, account, content, draft=True):
        if not hasattr(self, 'access_token'):
            if not self.authenticate(account['credentials']):
                return {'success': False, 'error': '认证失败'}
        
        title = content.get('title', '无标题')[:64]
        body = content.get('body', '')
        cover_image = content.get('cover_image', '')
        
        html_content = self.create_article_html(title, body, cover_image)
        
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"
        
        article = {
            'title': title,
            'content': html_content,
            'author': content.get('author', '小洛')[:8],
            'need_open_comment': 1,
            'only_fans_can_comment': 0
        }
        
        thumb_id = account['credentials'].get('default_thumb_media_id')
        if thumb_id and thumb_id.strip():
            article['thumb_media_id'] = thumb_id
        
        digest = content.get('digest', '')
        if digest:
            article['digest'] = digest[:120]
        
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
                'message': '文章已创建为草稿，请登录公众号后台发布'
            }
        return {'success': False, 'error': result.get('errmsg', '未知错误')}
