---
name: publisher-skill
description: |
  PubClaw - 跨平台自媒体内容发布技能。支持微信公众号、小红书、抖音、雪球、快手等多平台一键发布。
  
  核心功能：
  1. 多平台账号管理（加密存储、自动续签、权限校验）
  2. 内容智能适配（Markdown转各平台格式、规则适配）
  3. 发布执行引擎（API调用、失败重试、并发控制）
  4. 状态监控告警（日志记录、异常告警、资源监控）
  
  支持平台：微信公众号（已支持）、小红书、抖音、雪球、快手（待扩展）
  
  部署方式：服务端部署，支持API调用和定时任务
  
  触发条件：当用户提到"发布文章"、"多平台发布"、"PubClaw"、"内容分发"等关键词时触发。
---

# PubClaw - 跨平台自媒体发布技能

## 项目概述

**PubClaw** 是一个开源的跨平台自媒体内容发布工具，旨在解决内容创作者多平台分发的痛点。

### 核心优势

- 🚀 **跨平台**：一次编写，多平台发布
- 🔒 **安全**：账号信息加密存储，支持自动续签
- 🧠 **智能**：自动适配各平台格式和规则
- 📊 **可监控**：完整的发布日志和状态追踪
- 🔌 **可扩展**：插件化架构，易于添加新平台

### 支持平台

| 平台 | 状态 | 特性 |
|------|------|------|
| 微信公众号 | ✅ 已支持 | 图文、草稿、发布 |
| 小红书 | 🚧 开发中 | 图文、视频 |
| 抖音 | 📋 规划中 | 视频、图文 |
| 雪球 | 📋 规划中 | 帖子、长文 |
| 快手 | 📋 规划中 | 视频 |
| B站 | 📋 规划中 | 专栏、视频 |

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
│  CLI工具 / Web界面 / OpenClaw API / 定时任务                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    PubClaw Core                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 账号管理服务  │  │ 内容适配服务  │  │ 发布执行服务  │      │
│  │ AccountMgr   │  │  ContentAdapter│  │   Publisher  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ 状态监控服务  │  │  平台适配器   │                         │
│  │   Monitor    │  │  PlatformAdapters                      │
│  └──────────────┘  └──────────────┘                         │
└──────────────────┬──────────────────────────────────────────┘
                   │
    ┌──────────────┼──────────────┬──────────────┐
    │              │              │              │
┌───▼────┐   ┌────▼────┐   ┌─────▼────┐   ┌────▼────┐
│ 微信API │   │小红书API│   │ 抖音API  │   │其他API  │
└─────────┘   └─────────┘   └──────────┘   └─────────┘
```

### 核心模块

#### 1. 账号管理服务 (AccountManager)

**职责**：
- 多平台账号加密存储（AES-256）
- 登录状态维护与自动续签
- 账号权限校验与分组管理
- 风控状态监控

**数据模型**：
```json
{
  "account_id": "wechat_001",
  "platform": "wechat",
  "account_type": "subscription",
  "credentials": {
    "app_id": "xxx",
    "app_secret": "xxx",
    "access_token": "xxx",
    "expires_at": 1234567890
  },
  "status": "active",
  "group": "personal",
  "created_at": "2026-03-14T10:00:00Z",
  "last_used": "2026-03-14T18:00:00Z"
}
```

#### 2. 内容适配服务 (ContentAdapter)

**职责**：
- 统一内容格式转换（Markdown → 各平台格式）
- 平台规则适配（字数限制、图片尺寸、标签处理）
- 内容审核预检查

**适配规则示例**：
```python
ADAPTER_RULES = {
    "wechat": {
        "title_max": 64,
        "content_max": 20000,
        "image_width": 900,
        "support_html": True,
        "support_markdown": False
    },
    "xiaohongshu": {
        "title_max": 20,
        "content_max": 1000,
        "image_ratio": "3:4",
        "hashtag_max": 10,
        "support_html": False
    }
}
```

#### 3. 发布执行服务 (Publisher)

**职责**：
- 调用平台发布接口
- 失败重试机制（指数退避）
- 并发控制（令牌桶算法）
- 发布状态实时反馈

**重试策略**：
- 网络异常：立即重试，最多3次
- 频率限制：等待60秒后重试
- 内容违规：标记失败，人工介入

#### 4. 状态监控服务 (Monitor)

**职责**：
- 发布过程日志记录
- 账号异常告警（登录失效、风控限制）
- 系统资源监控
- 统计报表生成

---

## 快速开始

### 环境要求

- Python 3.9+
- Redis（可选，用于缓存和队列）
- Linux/macOS/Windows

### 安装部署

```bash
# 克隆仓库
git clone https://github.com/yiji1100/PubClaw.git
cd PubClaw

# 安装依赖
pip install -r requirements.txt

# 初始化配置
cp config.example.yaml config.yaml
# 编辑 config.yaml，填入你的账号信息

# 启动服务
python -m pubclaw.server
```

### 基础使用

**方式1：命令行**
```bash
# 发布单篇文章
pubclaw publish --platform wechat --file article.md

# 多平台同时发布
pubclaw publish --platforms wechat,xiaohongshu,douyin --file article.md

# 查看发布状态
pubclaw status --task-id task_20260314_001
```

**方式2：Python API**
```python
from pubclaw import Publisher

publisher = Publisher()

# 单平台发布
result = publisher.publish(
    platform="wechat",
    content={
        "title": "今日市场分析",
        "content": "# 标题\n正文内容...",
        "cover_image": "/path/to/cover.jpg"
    }
)

# 多平台发布
results = publisher.publish_multi(
    platforms=["wechat", "xiaohongshu", "snowball"],
    content=article_content
)
```

**方式3：HTTP API**
```bash
curl -X POST http://localhost:8080/api/v1/publish \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "platforms": ["wechat"],
    "content": {
      "title": "今日市场分析",
      "body": "# 标题\n正文...",
      "cover": "https://example.com/cover.jpg"
    }
  }'
```

---

## 配置说明

### 基础配置 (config.yaml)

```yaml
server:
  host: "0.0.0.0"
  port: 8080
  debug: false

security:
  secret_key: "your-secret-key-here"
  token_expiry: 3600

storage:
  type: "sqlite"  # sqlite / mysql / postgresql
  path: "./data/pubclaw.db"

platforms:
  wechat:
    enabled: true
    app_id: "${WECHAT_APP_ID}"
    app_secret: "${WECHAT_APP_SECRET}"
    default_thumb_media_id: "${WECHAT_THUMB_ID}"
    
  xiaohongshu:
    enabled: false
    # 配置项...
    
  douyin:
    enabled: false
    # 配置项...

publishing:
  retry_times: 3
  retry_interval: 60
  concurrent_limit: 5
  
monitoring:
  log_level: "INFO"
  alert_channels:
    - type: "webhook"
      url: "${ALERT_WEBHOOK_URL}"
```

### 环境变量

```bash
export WECHAT_APP_ID="wxb89345756f6c43a7"
export WECHAT_APP_SECRET="876acfdbb10c17b586986849f654d6f6"
export PUBCLAW_SECRET_KEY="your-secret-key"
export ALERT_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
```

---

## 平台适配指南

### 添加新平台步骤

1. **创建适配器类**
```python
# pubclaw/platforms/new_platform.py
from .base import BasePlatform

class NewPlatformAdapter(BasePlatform):
    name = "new_platform"
    display_name = "新平台"
    
    async def authenticate(self, credentials):
        # 实现认证逻辑
        pass
    
    async def publish_content(self, content, options=None):
        # 实现发布逻辑
        pass
    
    async def get_status(self, post_id):
        # 实现状态查询
        pass
```

2. **注册适配器**
```python
# pubclaw/platforms/__init__.py
from .new_platform import NewPlatformAdapter

PLATFORM_ADAPTERS = {
    "wechat": WechatAdapter,
    "new_platform": NewPlatformAdapter,
}
```

3. **添加适配规则**
```python
# pubclaw/adapters/rules.py
ADAPTER_RULES["new_platform"] = {
    "title_max": 50,
    "content_max": 5000,
    "image_formats": ["jpg", "png"],
    "support_topics": True
}
```

---

## API文档

详见 [API.md](./docs/API.md)

### 核心端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/publish` | POST | 发布内容 |
| `/api/v1/tasks/{id}` | GET | 查询任务状态 |
| `/api/v1/accounts` | GET/POST | 账号管理 |
| `/api/v1/stats` | GET | 统计数据 |
| `/health` | GET | 健康检查 |

---

## 部署指南

### 服务器部署

```bash
# 1. 上传代码到服务器
scp -r ./PubClaw root@101.34.54.108:/opt/

# 2. 安装依赖
ssh root@101.34.54.108
cd /opt/PubClaw
pip install -r requirements.txt

# 3. 配置服务
cp config.example.yaml config.yaml
nano config.yaml  # 编辑配置

# 4. 启动服务
python -m pubclaw.server

# 或使用 systemd
systemctl start pubclaw
```

### Docker部署

```bash
# 构建镜像
docker build -t pubclaw:latest .

# 运行容器
docker run -d \
  --name pubclaw \
  -p 8080:8080 \
  -v ./config.yaml:/app/config.yaml \
  -v ./data:/app/data \
  pubclaw:latest
```

---

## 开发指南

### 项目结构

```
PubClaw/
├── pubclaw/                 # 核心代码
│   ├── __init__.py
│   ├── server.py           # HTTP服务
│   ├── core/               # 核心模块
│   │   ├── __init__.py
│   │   ├── account_mgr.py  # 账号管理
│   │   ├── content_adapter.py
│   │   ├── publisher.py
│   │   └── monitor.py
│   ├── platforms/          # 平台适配器
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── wechat.py
│   │   ├── xiaohongshu.py
│   │   └── ...
│   ├── adapters/           # 内容适配器
│   │   ├── __init__.py
│   │   ├── markdown.py
│   │   └── rules.py
│   └── utils/              # 工具函数
│       ├── __init__.py
│       ├── crypto.py
│       └── logger.py
├── scripts/                # 部署脚本
│   ├── deploy.sh
│   └── install.sh
├── tests/                  # 测试用例
├── docs/                   # 文档
├── config.example.yaml     # 配置示例
├── requirements.txt        # 依赖
├── Dockerfile
└── README.md
```

### 开发规范

- 遵循 PEP 8 代码规范
- 使用 Type Hints 类型注解
- 异步编程（asyncio）
- 单元测试覆盖率 > 80%

---

## 安全说明

### 数据安全

- 所有账号凭据使用 AES-256 加密存储
- 密钥通过环境变量传入，不硬编码
- 支持 HTTPS 传输
- 定期轮换访问令牌

### 风控策略

- 频率限制：单账号每分钟最多发布1次
- 并发控制：避免触发平台风控
- 异常检测：自动识别登录失效、验证码等情况
- 人工介入：异常状态自动通知管理员

---

## 贡献指南

欢迎提交 Issue 和 PR！

### 提交规范

- 使用语义化版本（Semantic Versioning）
- 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)
- 大功能先开 Issue 讨论

---

## 许可证

MIT License

---

## 联系方式

- GitHub: https://github.com/yiji1100/PubClaw
- 问题反馈: [Issues](https://github.com/yiji1100/PubClaw/issues)

---

**让内容创作更高效，让多平台发布更简单！** 🚀
