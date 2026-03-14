# PubClaw - 跨平台自媒体发布工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> 一次编写，多平台发布。让内容创作更高效。

## ✨ 特性

- 🚀 **跨平台发布**：一次编写，发布到微信、小红书、抖音等多个平台
- 🔒 **安全存储**：账号信息管理，支持多账号切换
- 🧠 **智能适配**：自动转换Markdown为各平台格式
- 📊 **状态监控**：完整的发布日志
- 🔌 **易于扩展**：插件化架构，轻松添加新平台

## 📦 支持平台

| 平台 | 状态 | 功能 |
|------|------|------|
| 微信公众号 | ✅ 已支持 | 图文、草稿 |
| 小红书 | 🚧 开发中 | 图文、视频 |
| 抖音 | 📋 规划中 | 视频 |
| 雪球 | 📋 规划中 | 帖子 |
| B站 | 📋 规划中 | 专栏、视频 |

---

## 🚀 快速开始

### 方式一：服务器部署（推荐）

适用于需要长期运行、定时发布的场景。

```bash
# 1. 登录服务器
ssh root@your-server-ip

# 2. 一键安装
cd /opt
git clone https://github.com/yiji1100/PubClaw.git

# 3. 安装依赖
cd PubClaw
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. 创建CLI工具
sudo ln -s $(pwd)/pubclaw /usr/local/bin/pubclaw
```

### 方式二：本地使用

```bash
# 克隆仓库
git clone https://github.com/yiji1100/PubClaw.git
cd PubClaw

# 安装依赖
pip install -r requirements.txt

# 使用Python直接运行
python -m pubclaw --help
```

---

## 📖 使用方法

### 1. 配置微信公众号

**步骤1：获取必要信息**
- 登录 [微信公众平台](https://mp.weixin.qq.com)
- 开发 → 基本配置 → 获取 `AppID` 和 `AppSecret`
- 确保服务器IP已加入白名单

**步骤2：配置账号**

```bash
pubclaw account --add --platform wechat
# 按提示输入 AppID 和 AppSecret
```

或通过Python配置：

```python
from pubclaw.core.account_mgr import AccountManager

mgr = AccountManager()
mgr.add_account(
    platform='wechat',
    account_id='default',
    credentials={
        'app_id': 'wx-your-app-id',
        'app_secret': 'your-app-secret',
        'default_thumb_media_id': ''  # 封面图MediaID，见下文
    }
)
```

### 2. 上传封面图（重要！）

微信公众号发布文章**必须**有封面图。

**获取MediaID步骤：**

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 内容与互动 → 素材库 → 图片
3. 上传封面图片
4. 点击上传的图片 → 复制 **Media ID**

**配置封面图：**

编辑账号配置文件：
```bash
nano ~/.pubclaw/accounts.json
```

修改为：
```json
{
  "wechat": [{
    "account_id": "default",
    "credentials": {
      "app_id": "wx-your-app-id",
      "app_secret": "your-app-secret",
      "default_thumb_media_id": "jJkiAf6vGD9J6-9-Ip37JC7iuz..."
    }
  }]
}
```

### 3. 发布文章

**准备Markdown文件：**

```markdown
# 文章标题

这里是正文内容。

## 二级标题

- 列表项1
- 列表项2

**粗体文字**

> 引用内容
```

**命令行发布：**

```bash
pubclaw publish --platform wechat --file article.md
```

**Python代码发布：**

```python
from pubclaw.core.account_mgr import AccountManager
from pubclaw.platforms.wechat import WechatAdapter

# 获取账号
mgr = AccountManager()
account = mgr.get_active_account('wechat')

# 读取文章
with open('article.md', 'r') as f:
    content = f.read()

# 发布
adapter = WechatAdapter()
result = adapter.publish(
    account=account,
    content={'title': '文章标题', 'body': content},
    draft=True  # True=创建草稿, False=直接发布
)

if result['success']:
    print(f"发布成功！Media ID: {result['media_id']}")
else:
    print(f"发布失败: {result['error']}")
```

### 4. 查看已配置账号

```bash
pubclaw account --list
```

输出示例：
```
平台            | 账号ID               | 状态
--------------------------------------------------
wechat         | default              | active
```

---

## 🏗️ 项目架构

```
PubClaw/
├── pubclaw/
│   ├── core/
│   │   ├── account_mgr.py    # 账号管理
│   │   └── publisher.py      # 发布执行
│   ├── platforms/
│   │   ├── base.py           # 平台适配器基类
│   │   └── wechat.py         # 微信公众号适配器
│   └── __main__.py           # CLI入口
├── scripts/
│   └── deploy.sh             # 部署脚本
├── requirements.txt          # 依赖列表
└── README.md                 # 本文档
```

### 核心模块说明

| 模块 | 功能 | 文件 |
|------|------|------|
| AccountManager | 账号的增删改查、持久化存储 | `core/account_mgr.py` |
| WechatAdapter | 微信公众号API对接、内容发布 | `platforms/wechat.py` |
| Publisher | 发布流程控制、错误处理 | `core/publisher.py` |

---

## 🔧 配置说明

### 环境变量

```bash
export PUBCLAW_SECRET_KEY="your-secret-key"  # 加密密钥
```

### 账号配置文件

位置：`~/.pubclaw/accounts.json`

```json
{
  "wechat": [
    {
      "account_id": "default",
      "platform": "wechat",
      "credentials": {
        "app_id": "wx-xxx",
        "app_secret": "xxx",
        "default_thumb_media_id": "xxx"
      },
      "status": "active"
    }
  ]
}
```

---

## 📝 文章格式支持

### Markdown语法

PubClaw支持标准Markdown语法，并自动转换为微信公众号格式：

| Markdown | 微信效果 |
|----------|----------|
| `# 标题` | 大号标题 |
| `## 二级标题` | 中号标题 |
| `**粗体**` | 绿色粗体 |
| `- 列表` | 无序列表 |
| `> 引用` | 绿色边框引用块 |
| `` `代码` `` | 灰色背景代码 |

### 文章要求

- **标题**：最多64个字符
- **作者**：最多8个字符
- **内容**：支持Markdown，自动转HTML
- **封面图**：必须通过素材库上传获取MediaID

---

## 🐛 常见问题

### Q1: 发布失败，提示 "invalid media_id"

**原因**：没有配置封面图或MediaID错误

**解决**：
1. 登录公众号后台上传封面图
2. 获取正确的MediaID
3. 更新 `~/.pubclaw/accounts.json`

### Q2: 提示 "api unauthorized"

**原因**：服务器IP未加入微信白名单

**解决**：
1. 开发 → 基本配置 → IP白名单
2. 添加服务器公网IP

### Q3: 认证失败

**原因**：AppID或AppSecret错误

**解决**：
1. 检查基本配置中的AppID和AppSecret
2. 确保AppSecret没有泄露被重置

### Q4: 如何查看素材列表获取MediaID？

```python
import requests

# 获取access_token
token_url = 'https://api.weixin.qq.com/cgi-bin/token'
params = {
    'grant_type': 'client_credential',
    'appid': 'your-app-id',
    'secret': 'your-app-secret'
}
resp = requests.get(token_url, params=params)
access_token = resp.json()['access_token']

# 获取图片素材列表
media_url = f'https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={access_token}'
data = {'type': 'image', 'offset': 0, 'count': 20}
resp = requests.post(media_url, json=data)
print(resp.json())
```

---

## 🤝 贡献

欢迎提交 Issue 和 PR！

## 📄 许可证

[MIT License](LICENSE)

---

**让内容分发更简单** 🎉
