import requests
import json
import markdown
import re

class WechatAdapter:
    name = 'wechat'
    
    # 微信公众号样式模板 - 优化版
    WECHAT_CSS = """
    <style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
        font-size: 17px;
        line-height: 2;
        color: #333;
        max-width: 100%;
        margin: 0;
        padding: 20px 16px;
        background: #fff;
    }
    h1 {
        font-size: 26px;
        font-weight: bold;
        color: #1a1a1a;
        margin: 40px 0 24px;
        padding-bottom: 16px;
        border-bottom: 3px solid #07c160;
        line-height: 1.5;
    }
    h2 {
        font-size: 22px;
        font-weight: bold;
        color: #2c2c2c;
        margin: 36px 0 20px;
        padding: 12px 0 12px 16px;
        border-left: 5px solid #07c160;
        background: linear-gradient(90deg, #f0f9f0 0%, transparent 100%);
        line-height: 1.5;
    }
    h3 {
        font-size: 19px;
        font-weight: bold;
        color: #444;
        margin: 28px 0 16px;
        line-height: 1.5;
    }
    p {
        margin: 20px 0;
        text-align: justify;
        text-indent: 2em;
        line-height: 2;
    }
    p:first-of-type {
        text-indent: 0;
    }
    strong {
        color: #07c160;
        font-weight: bold;
    }
    em {
        color: #666;
        font-style: italic;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 28px 0;
        font-size: 15px;
        background: #fafafa;
        border-radius: 8px;
        overflow: hidden;
    }
    th, td {
        border: 1px solid #e0e0e0;
        padding: 14px 16px;
        text-align: left;
        line-height: 1.6;
    }
    th {
        background: linear-gradient(135deg, #07c160 0%, #05a050 100%);
        color: white;
        font-weight: bold;
        font-size: 15px;
    }
    tr:nth-child(even) {
        background: #f5f5f5;
    }
    tr:hover {
        background: #e8f5e8;
    }
    blockquote {
        border-left: 5px solid #07c160;
        background: linear-gradient(135deg, #f0f9f0 0%, #e8f5e8 100%);
        padding: 20px 24px;
        margin: 28px 0;
        color: #444;
        font-size: 16px;
        border-radius: 0 12px 12px 0;
        line-height: 1.8;
    }
    blockquote p {
        text-indent: 0;
        margin: 12px 0;
    }
    code {
        background: #f5f5f5;
        padding: 3px 8px;
        border-radius: 4px;
        font-family: 'SF Mono', Monaco, monospace;
        font-size: 15px;
        color: #e83e8c;
    }
    pre {
        background: #2d2d2d;
        color: #f8f8f2;
        padding: 20px;
        border-radius: 12px;
        overflow-x: auto;
        font-size: 15px;
        line-height: 1.6;
        margin: 24px 0;
    }
    pre code {
        background: transparent;
        color: inherit;
        padding: 0;
    }
    ul, ol {
        margin: 24px 0;
        padding-left: 32px;
    }
    li {
        margin: 12px 0;
        line-height: 2;
    }
    a {
        color: #07c160;
        text-decoration: none;
        border-bottom: 1px solid #07c160;
        padding-bottom: 1px;
    }
    a:hover {
        background: #f0f9f0;
    }
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 28px auto;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    hr {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 40px 0;
    }
    /* 提示框样式 */
    .tip-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 5px solid #2196f3;
        padding: 20px 24px;
        margin: 28px 0;
        border-radius: 0 12px 12px 0;
        line-height: 1.8;
    }
    .warning-box {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border-left: 5px solid #f44336;
        padding: 20px 24px;
        margin: 28px 0;
        border-radius: 0 12px 12px 0;
        line-height: 1.8;
    }
    /* 延伸阅读区域 */
    .related-reading {
        background: linear-gradient(135deg, #f5f5f5 0%, #fafafa 100%);
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 24px;
        margin: 32px 0;
    }
    .related-reading h3 {
        margin-top: 0;
        color: #07c160;
        border-bottom: 2px solid #07c160;
        padding-bottom: 12px;
    }
    .related-reading ul {
        margin: 16px 0 0 0;
        padding-left: 0;
        list-style: none;
    }
    .related-reading li {
        margin: 12px 0;
        padding-left: 20px;
        position: relative;
    }
    .related-reading li:before {
        content: "📎";
        position: absolute;
        left: 0;
    }
    /* 二维码区域 */
    .qrcode-section {
        text-align: center;
        padding: 32px 24px;
        margin: 32px 0;
        background: linear-gradient(135deg, #f0f9f0 0%, #e8f5e8 100%);
        border-radius: 12px;
    }
    .qrcode-section h3 {
        margin-top: 0;
        color: #07c160;
    }
    .qrcode-section img {
        margin: 20px auto;
        max-width: 200px;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .qrcode-section p {
        text-indent: 0;
        margin: 16px 0 0 0;
        color: #666;
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
        """
        # 1. Markdown转HTML
        html = markdown.markdown(body, extensions=['tables', 'fenced_code', 'nl2br'])
        
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
        
        return html
    
    def create_article_html(self, title, body):
        """
        创建完整的微信公众号文章HTML
        """
        content_html = self.format_content(body)
        
        full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{self.WECHAT_CSS}
</head>
<body>
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
        
        # 使用自动排版生成HTML
        html_content = self.create_article_html(title, body)
        
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
