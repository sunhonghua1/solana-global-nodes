#!/bin/bash
# ==============================================
# 边缘节点一键部署脚本 (香港/大阪/莱比锡)
# Edge Node One-Click Deployment
# ==============================================

set -e

# 检测节点位置参数
NODE_LOCATION=${1:-"UNKNOWN"}

echo "🚀 开始部署 ${NODE_LOCATION} 边缘节点..."

# 1. 安装依赖
echo "📦 安装依赖..."
sudo apt update
sudo apt install python3-pip -y
pip3 install redis pyyaml

# 2. 根据节点选择配置文件
case $NODE_LOCATION in
    "HK"|"hk")
        cp config_hk.yaml config.yaml
        echo "📍 使用香港配置"
        ;;
    "JP"|"jp")
        cp config_jp.yaml config.yaml
        echo "📍 使用大阪配置"
        ;;
    "DE"|"de")
        cp config_de.yaml config.yaml
        echo "📍 使用莱比锡配置"
        ;;
    *)
        echo "⚠️ 未指定节点，使用默认配置"
        echo "用法: ./deploy_edge.sh [HK|JP|DE]"
        ;;
esac

# 3. 测试连接到 Master
echo "🔗 测试连接到洛杉矶 Master..."
python3 -c "
import redis
r = redis.Redis(host='74.48.178.153', port=6379, password='YourSuperSecretGlobalPassword2026!', socket_timeout=5)
print('PING:', r.ping())
print('✅ 连接成功!')
"

echo ""
echo "=========================================="
echo "✅ ${NODE_LOCATION} 边缘节点部署完成!"
echo "=========================================="
echo ""
echo "下一步: 运行 Publisher (发送报警)"
echo "  python3 publisher.py"
echo ""
