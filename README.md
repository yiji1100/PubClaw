# PubClaw - 跨平台自媒体发布工具

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> 一次编写，多平台发布。让内容创作更高效。

## ✨ 特性

- 🚀 **跨平台发布**：一次编写，发布到微信、小红书、抖音等多个平台
- 🔒 **安全存储**：账号信息AES-256加密，支持自动续签
- 🧠 **智能适配**：自动转换各平台格式，适配规则限制
- 📊 **状态监控**：完整的发布日志，异常自动告警
- 🔌 **易于扩展**：插件化架构，轻松添加新平台

## 📦 支持平台

| 平台 | 状态 | 功能 |
|------|------|------|
| 微信公众号 | ✅ 已支持 | 图文、草稿 |
| 小红书 | 🚧 开发中 | 图文、视频 |
| 抖音 | 📋 规划中 | 视频 |
| 雪球 | 📋 规划中 | 帖子 |
| B站 | 📋 规划中 | 专栏、视频 |

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yiji1100/PubClaw.git
cd PubClaw

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp config.example.yaml config.yaml
# 编辑 config.yaml
```

### 使用

**命令行**
```bash
# 发布到微信公众号
pubclaw publish --platform wechat --file article.md

# 多平台同时发布
pubclaw multi --platforms wechat,xiaohongshu --file article.md

# 查看状态
pubclaw status --task-id task_xxx
```

**Python API**
```python
from pubclaw import Publisher

publisher = Publisher()

# 单平台
result = publisher.publish(
    platform="wechat",
    content={
        "title": "今日市场分析",
        "body": "# 标题\n正文..."
    }
)
```

## 🏗️ 架构

```
PubClaw/
├── pubclaw/
│   ├── core/           # 核心模块
│   ├── platforms/      # 平台适配器
│   ├── adapters/       # 内容适配器
│   └── utils/          # 工具函数
├── scripts/            # 部署脚本
└── docs/               # 文档
```

## 📖 文档

- [快速开始](docs/quickstart.md)
- [API文档](docs/api.md)
- [部署指南](docs/deploy.md)
- [开发指南](docs/development.md)

## 🤝 贡献

欢迎提交 Issue 和 PR！

## 📄 许可证

[MIT License](LICENSE)

---

**让内容分发更简单** 🎉
