#!/usr/bin/env python3
"""
全球网络监控桥接器
将 TokenMonitor 检测到的新币通过 Redis 广播到全球网络
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# 添加 solana-sniper-bot 路径
sys.path.insert(0, os.path.expanduser('~/solana-sniper-bot/src'))

import redis
import yaml
from loguru import logger

# 导入现有的监控模块
from monitor import TokenMonitor, NewToken

# ============================================
# 配置
# ============================================

# Redis 配置 (连接洛杉矶 Master)
REDIS_CONFIG = {
    'host': '74.48.178.153',
    'port': 6379,
    'password': 'YourSuperSecretGlobalPassword2026!',
    'db': 0,
    'socket_timeout': 10
}

# 当前节点位置
NODE_LOCATION = os.getenv('NODE_LOCATION', 'DE')  # HK / JP / DE

# Redis 频道
CHANNEL_ALERTS = 'global_alerts'
CHANNEL_NEW_TOKENS = 'new_tokens'

# ============================================
# 全球广播器
# ============================================

class GlobalBroadcaster:
    """将本地检测的信号广播到全球网络"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=REDIS_CONFIG['host'],
            port=REDIS_CONFIG['port'],
            password=REDIS_CONFIG['password'],
            db=REDIS_CONFIG['db'],
            socket_timeout=REDIS_CONFIG['socket_timeout'],
            decode_responses=True
        )
        self.location = NODE_LOCATION
        logger.info(f"[{self.location}] 连接到 Redis Master...")
        
    def broadcast_new_token(self, token: NewToken):
        """广播新代币发现"""
        message = {
            'type': 'NEW_TOKEN',
            'source': self.location,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'address': token.address,
                'name': token.name,
                'symbol': token.symbol,
                'platform': token.platform,
                'liquidity': token.liquidity,
                'price': token.price
            }
        }
        
        try:
            receivers = self.redis_client.publish(CHANNEL_NEW_TOKENS, json.dumps(message))
            logger.success(f"[{self.location}] 🚀 广播新币 {token.symbol} -> {receivers} 个接收者")
        except Exception as e:
            logger.error(f"[{self.location}] ❌ 广播失败: {e}")
            
    def broadcast_alert(self, alert_type: str, data: dict):
        """广播通用报警"""
        message = {
            'type': alert_type,
            'source': self.location,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            receivers = self.redis_client.publish(CHANNEL_ALERTS, json.dumps(message))
            logger.info(f"[{self.location}] 📡 广播报警 {alert_type} -> {receivers} 个接收者")
        except Exception as e:
            logger.error(f"[{self.location}] ❌ 广播失败: {e}")

# ============================================
# 主程序
# ============================================

broadcaster = GlobalBroadcaster()

async def on_new_token_detected(token: NewToken):
    """当检测到新币时的回调"""
    logger.info(f"🆕 检测到新币: {token.symbol} ({token.platform})")
    
    # 广播到全球网络
    broadcaster.broadcast_new_token(token)

async def main():
    """主入口"""
    logger.info(f"="*50)
    logger.info(f"🌍 全球监控节点启动 - 位置: {NODE_LOCATION}")
    logger.info(f"="*50)
    
    # 加载 sniper-bot 配置
    config_path = os.path.expanduser('~/solana-sniper-bot/config/config.yaml')
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info("✅ 加载 sniper-bot 配置成功")
    else:
        logger.warning("⚠️ 找不到 config.yaml，使用默认配置")
        config = {
            'platforms': {'pump_fun': True, 'raydium': True},
            'filters': {'min_liquidity': 1000},
            'rpc': {'helius_api_key': ''}
        }
    
    # 创建监控器
    monitor = TokenMonitor(config, on_new_token_detected)
    
    logger.info("🔍 开始监控 Pump.fun 和 Raydium...")
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("停止监控...")
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())
