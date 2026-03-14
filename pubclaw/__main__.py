#!/usr/bin/env python3
"""
PubClaw - 跨平台自媒体发布工具
主程序入口
"""

import asyncio
import argparse
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from pubclaw.core.publisher import Publisher
from pubclaw.core.account_mgr import AccountManager
from pubclaw.utils.logger import setup_logger

logger = setup_logger(__name__)


async def main():
    parser = argparse.ArgumentParser(description='PubClaw - 跨平台自媒体发布工具')
    parser.add_argument('--config', '-c', default='config.yaml', help='配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # publish 命令
    publish_parser = subparsers.add_parser('publish', help='发布内容')
    publish_parser.add_argument('--platform', '-p', required=True, help='平台名称')
    publish_parser.add_argument('--file', '-f', required=True, help='内容文件路径')
    publish_parser.add_argument('--draft', '-d', action='store_true', help='创建草稿')
    
    # multi 命令
    multi_parser = subparsers.add_parser('multi', help='多平台发布')
    multi_parser.add_argument('--platforms', '-p', required=True, help='平台列表，逗号分隔')
    multi_parser.add_argument('--file', '-f', required=True, help='内容文件路径')
    
    # account 命令
    account_parser = subparsers.add_parser('account', help='账号管理')
    account_parser.add_argument('--list', '-l', action='store_true', help='列出账号')
    account_parser.add_argument('--add', '-a', action='store_true', help='添加账号')
    account_parser.add_argument('--platform', '-p', help='平台名称')
    
    # status 命令
    status_parser = subparsers.add_parser('status', help='查看状态')
    status_parser.add_argument('--task-id', '-t', help='任务ID')
    
    # server 命令
    server_parser = subparsers.add_parser('server', help='启动HTTP服务')
    server_parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    server_parser.add_argument('--port', '-p', type=int, default=8080, help='监听端口')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'server':
        from pubclaw.server import start_server
        await start_server(args.host, args.port, args.config)
    
    elif args.command == 'publish':
        await cmd_publish(args)
    
    elif args.command == 'multi':
        await cmd_multi(args)
    
    elif args.command == 'account':
        await cmd_account(args)
    
    elif args.command == 'status':
        await cmd_status(args)


async def cmd_publish(args):
    """单平台发布"""
    publisher = Publisher(config_path=args.config)
    
    # 读取内容
    with open(args.file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    result = await publisher.publish(
        platform=args.platform,
        content=content,
        draft=args.draft
    )
    
    if result['success']:
        logger.info(f"✅ 发布成功: {result['task_id']}")
    else:
        logger.error(f"❌ 发布失败: {result['error']}")


async def cmd_multi(args):
    """多平台发布"""
    publisher = Publisher(config_path=args.config)
    
    platforms = [p.strip() for p in args.platforms.split(',')]
    
    with open(args.file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = await publisher.publish_multi(
        platforms=platforms,
        content=content
    )
    
    for platform, result in results.items():
        status = "✅" if result['success'] else "❌"
        logger.info(f"{status} {platform}: {result.get('message', '')}")


async def cmd_account(args):
    """账号管理"""
    mgr = AccountManager(config_path=args.config)
    
    if args.list:
        accounts = await mgr.list_accounts()
        print("\n已配置账号：")
        print("-" * 50)
        for acc in accounts:
            print(f"  {acc['platform']:15} | {acc['account_id']:20} | {acc['status']}")
        print()
    
    elif args.add:
        # 交互式添加账号
        platform = args.platform or input("平台名称 (wechat/xiaohongshu/...): ")
        await mgr.add_account_interactive(platform)


async def cmd_status(args):
    """查看状态"""
    publisher = Publisher(config_path=args.config)
    
    if args.task_id:
        status = await publisher.get_task_status(args.task_id)
        print(f"\n任务状态: {args.task_id}")
        print(f"  状态: {status['status']}")
        print(f"  平台: {status['platform']}")
        print(f"  创建时间: {status['created_at']}")
        if status.get('published_at'):
            print(f"  发布时间: {status['published_at']}")
    else:
        # 显示系统状态
        stats = await publisher.get_stats()
        print("\n系统状态：")
        print(f"  今日发布: {stats['today_count']}")
        print(f"  成功率: {stats['success_rate']:.1f}%")
        print(f"  队列长度: {stats['queue_length']}")


if __name__ == '__main__':
    asyncio.run(main())
