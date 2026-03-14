import requests
import json
import markdown

class WechatAdapter:
    name = 'wechat'
    
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
    
    def publish(self, account, content, draft=True):
        if not hasattr(self, 'access_token'):
            if not self.authenticate(account['credentials']):
                return {'success': False, 'error': '认证失败'}
        
        title = content.get('title', '无标题')[:64]
        body = content.get('body', '')
        html = markdown.markdown(body, extensions=['tables'])
        
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"
        
        # 准备文章数据
        article = {
            'title': title,
            'content': html,
            'author': '小洛',
            'need_open_comment': 1
        }
        
        # 添加封面图（如果有）
        thumb_id = account['credentials'].get('default_thumb_media_id')
        if thumb_id and thumb_id.strip():
            article['thumb_media_id'] = thumb_id
        
        resp = requests.post(url, json={'articles': [article]}, timeout=30)
        result = resp.json()
        
        if 'media_id' in result:
            return {'success': True, 'media_id': result['media_id'], 'draft': True}
        return {'success': False, 'error': result.get('errmsg', '未知错误')}
