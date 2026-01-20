#!/bin/bash
# ==============================================
# 洛杉矶 Master 节点一键部署脚本
# LA Master Node One-Click Deployment
# ==============================================

set -e

echo "🚀 开始部署 Redis Master 节点..."

# 1. 安装 Redis
echo "📦 安装 Redis..."
sudo apt update
sudo apt install redis-server python3-pip -y

# 2. 备份原配置
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# 3. 修改 Redis 配置
echo "⚙️ 配置 Redis..."
sudo sed -i 's/^bind 127.0.0.1.*/bind 0.0.0.0/' /etc/redis/redis.conf
sudo sed -i 's/^# requirepass.*/requirepass YourSuperSecretGlobalPassword2026!/' /etc/redis/redis.conf
sudo sed -i 's/^requirepass.*/requirepass YourSuperSecretGlobalPassword2026!/' /etc/redis/redis.conf

# 4. 重启 Redis
echo "🔄 重启 Redis 服务..."
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# 5. 配置防火墙 (只允许指定IP)
echo "🔒 配置防火墙规则..."
sudo ufw allow from 205.198.66.34 to any port 6379 comment 'Hong Kong'
sudo ufw allow from 56.155.17.251 to any port 6379 comment 'Osaka'
sudo ufw allow from 104.28.207.215 to any port 6379 comment 'Leipzig WARP'
sudo ufw --force enable

# 6. 安装 Python 依赖
echo "🐍 安装 Python 依赖..."
pip3 install redis pyyaml

# 7. 使用 LA 配置
cp config_la.yaml config.yaml

# 8. 验证 Redis 是否正常
echo "✅ 验证 Redis 连接..."
redis-cli -a YourSuperSecretGlobalPassword2026! ping

echo ""
echo "=========================================="
echo "✅ 洛杉矶 Master 节点部署完成!"
echo "=========================================="
echo ""
echo "下一步: 运行 Subscriber (接收报警)"
echo "  python3 subscriber.py"
echo ""
