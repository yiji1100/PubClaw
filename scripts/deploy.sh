#!/bin/bash
# PubClaw 服务器部署脚本
# 部署地址：101.34.54.108

set -e

echo "🚀 PubClaw 服务器部署脚本"
echo "============================"

# 配置
SERVER_IP="101.34.54.108"
DEPLOY_DIR="/opt/pubclaw"
SERVICE_NAME="pubclaw"

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 root 权限运行"
    exit 1
fi

echo "📦 第1步：更新系统..."
apt-get update
apt-get install -y python3 python3-pip python3-venv git

echo "📁 第2步：创建部署目录..."
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

# 创建虚拟环境
echo "🐍 第3步：创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
echo "📥 第4步：安装依赖..."
pip install --upgrade pip
pip install requests markdown cryptography pyyaml schedule aiohttp

echo "⚙️ 第5步：创建目录结构..."
mkdir -p data logs config

echo "📝 第6步：创建配置文件..."
cat > config/config.yaml << 'EOF'
server:
  host: "0.0.0.0"
  port: 8080
  debug: false

security:
  secret_key: "${PUBCLAW_SECRET_KEY:-change-me-in-production}"
  token_expiry: 3600

storage:
  type: "sqlite"
  path: "./data/pubclaw.db"

platforms:
  wechat:
    enabled: true
    accounts:
      - account_id: "default"
        app_id: "${WECHAT_APP_ID}"
        app_secret: "${WECHAT_APP_SECRET}"
        default_thumb_media_id: "${WECHAT_THUMB_ID}"

publishing:
  retry_times: 3
  retry_interval: 60
  concurrent_limit: 3

monitoring:
  log_level: "INFO"
  log_file: "./logs/pubclaw.log"
EOF

echo "🔧 第7步：创建systemd服务..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=PubClaw - 跨平台自媒体发布服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${DEPLOY_DIR}
Environment=PYTHONPATH=${DEPLOY_DIR}
EnvironmentFile=${DEPLOY_DIR}/config/.env
ExecStart=${DEPLOY_DIR}/venv/bin/python -m pubclaw server --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=append:${DEPLOY_DIR}/logs/service.log
StandardError=append:${DEPLOY_DIR}/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

echo "📝 第8步：创建环境变量文件..."
cat > config/.env << 'EOF'
# 微信公众号配置
WECHAT_APP_ID=wxb89345756f6c43a7
WECHAT_APP_SECRET=876acfdbb10c17b586986849f654d6f6
WECHAT_THUMB_ID=

# 系统密钥（请修改为随机字符串）
PUBCLAW_SECRET_KEY=your-random-secret-key-here
EOF

chmod 600 config/.env

echo "🔧 第9步：创建CLI工具..."
cat > /usr/local/bin/pubclaw << 'EOF'
#!/bin/bash
cd /opt/pubclaw
source venv/bin/activate
python -m pubclaw "$@"
EOF
chmod +x /usr/local/bin/pubclaw

echo "🚀 第10步：启动服务..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}

echo ""
echo "✅ 部署完成！"
echo "============================"
echo ""
echo "📋 后续操作："
echo "1. 查看服务状态:"
echo "   systemctl status ${SERVICE_NAME}"
echo ""
echo "2. 查看日志:"
echo "   tail -f ${DEPLOY_DIR}/logs/pubclaw.log"
echo ""
echo "3. 使用CLI工具:"
echo "   pubclaw --help"
echo ""
echo "4. 添加微信公众号封面图:"
echo "   pubclaw account add --platform wechat"
echo ""
echo "5. 发布测试:"
echo "   pubclaw publish --platform wechat --file test.md"
echo ""
echo "⚠️  重要提醒："
echo "   - 请修改 config/.env 中的 PUBCLAW_SECRET_KEY"
echo "   - 上传封面图获取 media_id 后填入配置"
echo "   - 服务器IP ${SERVER_IP} 已加入微信白名单"
echo ""
