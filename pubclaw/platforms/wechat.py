import requests
import json
import markdown
import re

class WechatAdapter:
    name = 'wechat'
    
    # 优化后的微信公众号样式
    WECHAT_CSS = """
    <style>
    /* 基础重置 */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* 文章容器 */
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 16px;
        color: #333;
        line-height: 1.8;
        max-width: 100%;
        padding: 20px 16px;
        background: #fff;
    }
    
    /* 标题样式 - 层次分明 */
    h1 {
        font-size: 22px;
        font-weight: bold;
        color: #000;
        margin: 30px 0 20px;
        padding-bottom: 12px;
        border-bottom: 2px solid #07c160;
        line-height: 1.4;
    }
    
    h2 {
        font-size: 19px;
        font-weight: bold;
        color: #1a1a1a;
        margin: 28px 0 16px;
        padding: 10px 0 10px 14px;
        border-left: 4px solid #07c160;
        background: #f9f9f9;
        line-height: 1.4;
    }
    
    h3 {
        font-size: 17px;
        font-weight: bold;
        color: #333;
        margin: 22px 0 12px;
        line-height: 1.4;
    }
    
    h4 {
        font-size: 16px;
        font-weight: bold;
        color: #444;
        margin: 18px 0 10px;
        line-height: 1.4;
    }
    
    /* 段落样式 */
    p {
        margin: 14px 0;
        line-height: 1.8;
        color: #333;
        text-align: justify;
    }
    
    /* 列表样式 - 关键优化 */
    ul, ol {
        margin: 16px 0;
        padding-left: 28px;
    }
    
    li {
        margin: 10px 0;
        line-height: 1.8;
        color: #333;
    }
    
    /* 二级列表 */
    ul ul, ol ul, ul ol, ol ol {
        margin: 8px 0;
        padding-left: 20px;
    }
    
    ul ul li, ol ul li {
        margin: 6px 0;
        list-style-type: circle;
    }
    
    /* 强调样式 */
    strong {
        color: #07c160;
        font-weight: bold;
    }
    
    /* 引用块 */
    blockquote {
        margin: 20px 0;
        padding: 16px 20px;
        background: #f5f5f5;
        border-left: 4px solid #07c160;
        color: #555;
        font-size: 15px;
        line-height: 1.7;
    }
    
    blockquote p {
        margin: 8px 0;
    }
    
    /* 分割线 */
    hr {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 30px 0;
    }
    
    /* 表格样式 */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 14px;
        background: #fff;
    }
    
    th, td {
        border: 1px solid #ddd;
        padding: 12px 14px;
        text-align: left;
        line-height: 1.6;
    }
    
    th {
        background: #f5f5f5;
        font-weight: bold;
        color: #333;
    }
    
    tr:nth-child(even) {
        background: #fafafa;
    }
    
    /* 链接样式 */
    a {
        color: #07c160;
        text-decoration: none;
        border-bottom: 1px solid #07c160;
    }
    
    /* 图片样式 */
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 20px auto;
    }
    
    /* 首图 */
    .cover-image {
        margin: 0 0 20px 0;
    }
    
    .cover-image img {
        width: 100%;
        margin: 0;
    }
    
    /* 导语 */
    .intro {
        background: #f8f8f8;
        padding: 16px 20px;
        margin: 20px 0;
        border-radius: 4px;
        font-size: 15px;
        color: #555;
        line-height: 1.8;
    }
    
    /* 提示框 */
    .tip-box {
        background: #e8f5e9;
        border-left: 4px solid #07c160;
        padding: 16px 20px;
        margin: 20px 0;
        color: #2e7d32;
        line-height: 1.7;
    }
    
    .warning-box {
        background: #ffebee;
        border-left: 4px solid #f44336;
        padding: 16px 20px;
        margin: 20px 0;
        color: #c62828;
        line-height: 1.7;
    }
    
    /* 代码 */
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
        border-radius: 4px;
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
    
    /* 延伸阅读 */
    .related-reading {
        background: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 20px;
        margin: 25px 0;
    }
    
    .related-reading h3 {
        margin: 0 0 15px 0;
        color: #07c160;
        font-size: 17px;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 10px;
    }
    
    .related-reading ul {
        margin: 10px 0 0 0;
        padding-left: 0;
        list-style: none;
    }
    
    .related-reading li {
        margin: 8px 0;
        padding-left: 20px;
        position: relative;
        font-size: 15px;
    }
    
    .related-reading li:before {
        content: "→";
        position: absolute;
        left: 0;
        color: #07c160;
    }
    
    /* 二维码 */
    .qrcode-section {
        text-align: center;
        padding: 25px 20px;
        margin: 25px 0;
        background: #f5f5f5;
        border-radius: 4px;
    }
    
    .qrcode-section h3 {
        margin: 0 0 15px 0;
        color: #07c160;
        font-size: 17px;
    }
    
    .qrcode-section img {
        margin: 10px auto;
        max-width: 160px;
    }
    
    .qrcode-section p {
        margin: 10px 0 0 0;
        color: #666;
        font-size: 14px;
        text-align: center;
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
        智能排版
        """
        # Markdown转HTML
        html = markdown.markdown(body, extensions=['tables', 'fenced_code'])
        
        # 清理多余的br标签
        html = re.sub(r'<br\s*/?>\s*<br\s*/?>', '</p><p>', html)
        html = re.sub(r'<br\s*/?>', '', html)
        
        # 处理提示框
        html = re.sub(
            r'<p>💡\s*([^<]+)</p>',
            r'<div class="tip-box">💡 \1</div>',
            html
        )
        html = re.sub(
            r'<p>⚠️\s*([^<]+)</p>',
            r'<div class="warning-box">⚠️ \1</div>',
            html
        )
        
        # 表格包装
        html = re.sub(
            r'<table>(.+?)</table>',
            r'<div style="overflow-x:auto;"><table>\1</table></div>',
            html,
            flags=re.DOTALL
        )
        
        return html
    
    def create_article_html(self, title, body, cover_image=None):
        """
        创建完整的微信公众号文章HTML
        """
        content_html = self.format_content(body)
        
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
