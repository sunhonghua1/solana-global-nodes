#!/bin/bash
# ==============================================
# 使用 Screen 后台运行脚本
# Run with Screen (Background Mode)
# ==============================================

MODE=${1:-"subscriber"}
NODE=${2:-"LA"}

echo "🚀 以后台模式启动 ${MODE} (${NODE})..."

# 安装 screen (如果没有)
which screen > /dev/null || sudo apt install screen -y

case $MODE in
    "sub"|"subscriber")
        screen -dmS redis_sub python3 subscriber.py
        echo "✅ Subscriber 已在后台启动"
        echo "   查看: screen -r redis_sub"
        echo "   退出: Ctrl+A, D"
        ;;
    "pub"|"publisher")
        screen -dmS redis_pub python3 publisher.py
        echo "✅ Publisher 已在后台启动"
        echo "   查看: screen -r redis_pub"
        echo "   退出: Ctrl+A, D"
        ;;
    *)
        echo "用法: ./run_background.sh [sub|pub] [NODE_NAME]"
        ;;
esac
