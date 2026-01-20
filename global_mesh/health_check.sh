#!/bin/bash
# ==============================================
# 全球网络健康检查脚本
# Global Network Health Check
# ==============================================

echo "🌍 全球 Redis Mesh 网络健康检查"
echo "================================"

REDIS_HOST="74.48.178.153"
REDIS_PASS="YourSuperSecretGlobalPassword2026!"

# 检查 Redis Master
echo ""
echo "📡 检查 Redis Master (洛杉矶)..."
if redis-cli -h $REDIS_HOST -a $REDIS_PASS ping 2>/dev/null | grep -q "PONG"; then
    echo "   ✅ Master 在线"
else
    echo "   ❌ Master 离线或无法连接"
fi

# 检查订阅者数量
echo ""
echo "👥 当前活跃订阅者..."
SUBS=$(redis-cli -h $REDIS_HOST -a $REDIS_PASS pubsub numsub global_alerts 2>/dev/null | tail -1)
echo "   global_alerts 频道: ${SUBS:-0} 个订阅者"

# 检查各节点延迟
echo ""
echo "⏱️ 节点延迟测试..."

declare -A NODES
NODES["香港"]="205.198.66.34"
NODES["大阪"]="56.155.17.251"
NODES["莱比锡"]="104.28.207.215"

for name in "${!NODES[@]}"; do
    ip=${NODES[$name]}
    latency=$(ping -c 1 -W 2 $ip 2>/dev/null | grep 'time=' | sed 's/.*time=\([0-9.]*\).*/\1/')
    if [ -n "$latency" ]; then
        echo "   ${name} (${ip}): ${latency}ms"
    else
        echo "   ${name} (${ip}): 无法连接"
    fi
done

echo ""
echo "================================"
echo "检查完成!"
