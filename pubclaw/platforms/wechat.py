import requests
import json
import markdown
import re

class WechatAdapter:
    name = 'wechat'
    
    # 微信公众号样式模板 - 统一字体版本
    WECHAT_CSS = """
    <style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
        font-size: 16px;
        line-height: 1.75;
        color: #333;
        max-width: 100%;
        margin: 0;
        padding: 16px;
        background: #fff;
    }
    h1 {
        font-size: 22px;
        font-weight: bold;
        color: #1a1a1a;
        margin: 32px 0 20px;
        padding-bottom: 12px;
        border-bottom: 3px solid #07c160;
        line-height: 1.4;
    }
    h2 {
        font-size: 18px;
        font-weight: bold;
        color: #2c2c2c;
        margin: 28px 0 16px;
        padding: 10px 0 10px 12px;
        border-left: 4px solid #07c160;
        background: #f8f8f8;
        line-height: 1.4;
    }
    h3 {
        font-size: 16px;
        font-weight: bold;
        color: #444;
        margin: 24px 0 12px;
        line-height: 1.4;
    }
    p {
        font-size: 16px;
        margin: 16px 0;
        text-align: justify;
        line-height: 1.75;
        color: #333;
    }
    strong {
        color: #07c160;
        font-weight: bold;
        font-size: 16px;
    }
    em {
        color: #666;
        font-style: italic;
        font-size: 16px;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 20px 0;
        font-size: 14px;
        background: #fafafa;
    }
    th, td {
        border: 1px solid #e0e0e0;
        padding: 10px 12px;
        text-align: left;
        font-size: 14px;
        line-height: 1.6;
    }
    th {
        background: #07c160;
        color: white;
        font-weight: bold;
    }
    tr:nth-child(even) {
        background: #f5f5f5;
    }
    blockquote {
        border-left: 4px solid #07c160;
        background: #f8f8f8;
        padding: 16px 20px;
        margin: 20px 0;
        font-size: 15px;
        color: #555;
        line-height: 1.7;
    }
    blockquote p {
        font-size: 15px;
        margin: 8px 0;
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
        background: #2d2d2d;
        color: #f8f8f2;
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
        font-size: 14px;
    }
    ul, ol {
        margin: 16px 0;
        padding-left: 24px;
        font-size: 16px;
    }
    li {
        margin: 8px 0;
        line-height: 1.75;
        font-size: 16px;
    }
    a {
        color: #07c160;
        text-decoration: none;
        border-bottom: 1px solid #07c160;
        font-size: 16px;
    }
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 16px auto;
        border-radius: 8px;
    }
    hr {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 32px 0;
    }
    /* 提示框样式 */
    .tip-box {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 16px 20px;
        margin: 20px 0;
        font-size: 15px;
        line-height: 1.7;
    }
    .warning-box {
        background: #ffebee;
        border-left: 4px solid #f44336;
        padding: 16px 20px;
        margin: 20px 0;
        font-size: 15px;
        line-height: 1.7;
    }
    /* 首图样式 */
    .cover-image {
        margin: 0 0 24px 0;
        width: 100%;
    }
    .cover-image img {
        width: 100%;
        margin: 0;
        border-radius: 0;
    }
    /* 导语样式 */
    .intro {
        background: #f8f8f8;
        padding: 16px 20px;
        margin: 20px 0;
        border-radius: 8px;
        font-size: 15px;
        line-height: 1.8;
        color: #555;
    }
    /* 延伸阅读区域 */
    .related-reading {
        background: #f5f5f5;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin: 24px 0;
    }
    .related-reading h3 {
        margin-top: 0;
        color: #07c160;
        border-bottom: 2px solid #07c160;
        padding-bottom: 10px;
        font-size: 17px;
    }
    .related-reading ul {
        margin: 12px 0 0 0;
        padding-left: 0;
        list-style: none;
        font-size: 15px;
    }
    .related-reading li {
        margin: 10px 0;
        padding-left: 20px;
        position: relative;
        font-size: 15px;
        line-height: 1.6;
    }
    .related-reading li:before {
        content: "📎";
        position: absolute;
        left: 0;
    }
    .related-reading a {
        font-size: 15px;
    }
    /* 二维码区域 */
    .qrcode-section {
        text-align: center;
        padding: 24px;
        margin: 24px 0;
        background: #f0f9f0;
        border-radius: 8px;
    }
    .qrcode-section h3 {
        margin-top: 0;
        color: #07c160;
        font-size: 17px;
    }
    .qrcode-section img {
        margin: 16px auto;
        max-width: 180px;
        border-radius: 8px;
    }
    .qrcode-section p {
        text-align: center;
        margin: 12px 0 0 0;
        color: #666;
        font-size: 14px;
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
        智能排版：自动优化内容格式
        注意：不使用 nl2br，避免换行符转成 <br> 导致列表格式混乱
        """
        # 1. Markdown转HTML - 不使用 nl2br
        html = markdown.markdown(body, extensions=['tables', 'fenced_code'])
        
        # 2. 自动添加样式类
        # 将包含"注意"、"提示"的段落转换为提示框
        html = re.sub(
            r'<p>💡\s*([^<]+)</p>',
            r'<div class="tip-box">💡 \1</div>',
            html
        )
        
        # 将包含"⚠️"、"警告"的段落转换为警告框
        html = re.sub(
            r'<p>⚠️\s*([^<]+)</p>',
            r'<div class="warning-box">⚠️ \1</div>',
            html
        )
        
        # 3. 优化表格：添加响应式包装
        html = re.sub(
            r'<table>(.+?)</table>',
            r'<div style="overflow-x:auto;"><table>\1</table></div>',
            html,
            flags=re.DOTALL
        )
        
        # 4. 优化代码块
        html = html.replace('<pre><code>', '<pre><code class="hljs">')
        
        # 5. 清理多余的 <br> 标签（如果有）
        html = re.sub(r'<br\s*/?>\s*<br\s*/?>', '</p><p>', html)
        html = re.sub(r'<br\s*/?>', '', html)
        
        return html
    
    def create_article_html(self, title, body, cover_image=None):
        """
        创建完整的微信公众号文章HTML
        """
        content_html = self.format_content(body)
        
        # 添加首图（如果有）
        cover_html = ''
        if cover_image:
            cover_html = f'<div class="cover-image"><img src="{cover_image}" alt="封面"></div>'
        
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
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
        
        # 使用自动排版生成HTML
        html_content = self.create_article_html(title, body, cover_image)
        
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"
        
        # 准备文章数据
        article = {
            'title': title,
            'content': html_content,
            'author': content.get('author', '小洛')[:8],
            'need_open_comment': 1,
            'only_fans_can_comment': 0
        }
        
        # 添加封面图（如果有）
        thumb_id = account['credentials'].get('default_thumb_media_id')
        if thumb_id and thumb_id.strip():
            article['thumb_media_id'] = thumb_id
        
        # 添加摘要（如果有）
        digest = content.get('digest', '')
        if digest:
            article['digest'] = digest[:120]
        
        # 关键：使用ensure_ascii=False保持中文字符
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
