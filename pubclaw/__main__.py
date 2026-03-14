#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/opt/pubclaw')

from pubclaw.core.account_mgr import AccountManager
from pubclaw.platforms.wechat import WechatAdapter

def main():
    if len(sys.argv) < 2:
        print('Usage: pubclaw <command>')
        print('Commands: publish, account')
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'publish':
        # 默认发布到微信
        mgr = AccountManager()
        account = mgr.get_active_account('wechat')
        if not account:
            print('错误：没有配置微信账号')
            return
        
        # 读取文件
        file_path = '/tmp/test_article.md'
        if len(sys.argv) > 3 and sys.argv[2] == '--file':
            file_path = sys.argv[3]
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # 发布
        adapter = WechatAdapter()
        result = adapter.publish(account, {'body': content, 'title': '测试文章'})
        
        if result['success']:
            print(f"✅ 发布成功！")
            print(f"Media ID: {result['media_id']}")
            print("请登录公众号后台查看草稿")
        else:
            print(f"❌ 发布失败: {result.get('error', '未知错误')}")
    
    elif cmd == 'account':
        mgr = AccountManager()
        
        if '--list' in sys.argv:
            accounts = mgr.list_accounts()
            print(f"{'平台':<15} | {'账号ID':<20} | {'状态'}")
            print("-" * 50)
            for acc in accounts:
                print(f"{acc['platform']:<15} | {acc['account_id']:<20} | {acc['status']}")
        
        elif '--add' in sys.argv:
            print("添加微信账号")
            app_id = input('AppID: ').strip()
            app_secret = input('AppSecret: ').strip()
            
            mgr.add_account('wechat', 'default', {
                'app_id': app_id,
                'app_secret': app_secret,
                'default_thumb_media_id': ''
            })
            print("✅ 账号添加成功")

if __name__ == '__main__':
    main()
