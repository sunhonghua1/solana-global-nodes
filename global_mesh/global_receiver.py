#!/usr/bin/env python3
"""
全球网络接收器 (运行在洛杉矶)
接收全球节点广播的新币信号，触发 Telegram 通知和狙击交易
"""
import asyncio
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.expanduser('~/solana-sniper-bot/src'))

import redis
import yaml
from loguru import logger

# 尝试导入模块
try:
    from notifications import Notifier
    NOTIFIER_AVAILABLE = True
except ImportError:
    NOTIFIER_AVAILABLE = False
    logger.warning("无法导入 Notifier，Telegram 通知禁用")

try:
    from trader import Trader
    from solders.keypair import Keypair
    TRADER_AVAILABLE = True
except ImportError:
    TRADER_AVAILABLE = False
    logger.warning("无法导入 Trader，自动交易禁用")

# ============================================
# 配置
# ============================================

REDIS_CONFIG = {
    'host': '127.0.0.1',  # 本地 Redis (洛杉矶是 Master)
    'port': 6379,
    'password': 'YourSuperSecretGlobalPassword2026!',
    'db': 0,
    'socket_timeout': 10
}

# 订阅的频道
CHANNELS = ['global_alerts', 'new_tokens']

# ============================================
# 狙击配置
# ============================================

SNIPER_CONFIG = {
    'enabled': True,                    # 是否启用自动交易
    'buy_amount_sol': 0.01,             # 每次买入的 SOL 数量
    'min_liquidity': 1000,              # 最小流动性 (美元)
    'platforms': ['pump_fun', 'raydium'],  # 只买这些平台的币
    'auto_sell': False,                 # 是否自动卖出
    'take_profit_percent': 50,          # 止盈 %
    'stop_loss_percent': 10,            # 止损 %
}

# ============================================
# 全球接收器
# ============================================

class GlobalReceiver:
    """接收全球网络的信号并执行交易"""
    
    def __init__(self, config: dict):
        self.config = config
        self.redis_client = redis.Redis(
            host=REDIS_CONFIG['host'],
            port=REDIS_CONFIG['port'],
            password=REDIS_CONFIG['password'],
            db=REDIS_CONFIG['db'],
            socket_timeout=REDIS_CONFIG['socket_timeout'],
            decode_responses=True
        )
        self.pubsub = self.redis_client.pubsub()
        self.notifier = None
        self.trader = None
        self.positions = {}  # 记录持仓
        
    async def start(self):
        """启动接收器"""
        # 初始化 Telegram 通知
        if NOTIFIER_AVAILABLE:
            self.notifier = Notifier(self.config)
            await self.notifier.start()
        
        # 初始化交易模块
        if TRADER_AVAILABLE and SNIPER_CONFIG['enabled']:
            self.trader = Trader(self.config)
            await self.trader.start()
            
            # 加载钱包
            wallet_path = self.config.get('wallet', {}).get('keypair_path', '')
            if wallet_path and os.path.exists(wallet_path):
                try:
                    with open(wallet_path, 'r') as f:
                        keypair_data = json.load(f)
                    keypair = Keypair.from_bytes(bytes(keypair_data))
                    self.trader.set_wallet(keypair)
                    logger.info(f"✅ 钱包已加载: {str(keypair.pubkey())[:16]}...")
                except Exception as e:
                    logger.error(f"加载钱包失败: {e}")
            else:
                logger.warning("⚠️ 未配置钱包，将以模拟模式运行")
                
            logger.info(f"🎯 狙击模式已启用 - 每次买入: {SNIPER_CONFIG['buy_amount_sol']} SOL")
        else:
            logger.info("💤 狙击模式已禁用")
        
        # 订阅频道
        self.pubsub.subscribe(*CHANNELS)
        logger.info(f"📡 订阅频道: {CHANNELS}")
        
        # 开始监听
        logger.info("🌍 全球接收器启动，等待信号...")
        
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                await self.handle_message(message)
                
    async def handle_message(self, message):
        """处理收到的消息"""
        try:
            channel = message['channel']
            data = json.loads(message['data'])
            
            source = data.get('source', 'UNKNOWN')
            msg_type = data.get('type', 'UNKNOWN')
            timestamp = data.get('timestamp', '')
            payload = data.get('data', {})
            
            logger.info(f"⚡ [{source}] {msg_type} @ {timestamp}")
            
            if msg_type == 'NEW_TOKEN':
                await self.handle_new_token(source, payload)
            elif msg_type == 'PUMP_DETECTED':
                await self.handle_pump_alert(source, payload)
            else:
                logger.debug(f"未知消息类型: {msg_type}")
                
        except json.JSONDecodeError:
            logger.warning(f"无效 JSON: {message['data']}")
        except Exception as e:
            logger.error(f"处理消息错误: {e}")
            
    async def handle_new_token(self, source: str, data: dict):
        """处理新代币信号"""
        symbol = data.get('symbol', '???')
        address = data.get('address', '')
        platform = data.get('platform', '')
        liquidity = data.get('liquidity', 0)
        
        logger.success(f"🆕 收到新币信号 from {source}: {symbol} on {platform}")
        logger.info(f"   地址: {address[:20]}...")
        logger.info(f"   流动性: ${liquidity:,.0f}")
        
        # 发送 Telegram 通知
        if self.notifier:
            await self.notifier.notify_new_token(symbol, address, f"{platform} (via {source})", liquidity)
        
        # 检查是否应该自动买入
        should_buy = await self.should_snipe(data)
        
        if should_buy and self.trader:
            await self.execute_snipe(data)
            
    async def should_snipe(self, data: dict) -> bool:
        """判断是否应该狙击这个代币"""
        if not SNIPER_CONFIG['enabled']:
            return False
            
        platform = data.get('platform', '')
        liquidity = data.get('liquidity', 0)
        address = data.get('address', '')
        
        # 检查平台
        if platform not in SNIPER_CONFIG['platforms']:
            logger.debug(f"跳过: 平台 {platform} 不在白名单")
            return False
            
        # 检查流动性
        if liquidity < SNIPER_CONFIG['min_liquidity']:
            logger.debug(f"跳过: 流动性 ${liquidity} < ${SNIPER_CONFIG['min_liquidity']}")
            return False
            
        # 检查是否已持仓
        if address in self.positions:
            logger.debug(f"跳过: 已持仓 {address[:16]}...")
            return False
            
        return True
        
    async def execute_snipe(self, data: dict):
        """执行狙击交易"""
        address = data.get('address', '')
        symbol = data.get('symbol', 'NEW')
        buy_amount = SNIPER_CONFIG['buy_amount_sol']
        
        logger.warning(f"🎯 开始狙击 {symbol} ({address[:16]}...) - {buy_amount} SOL")
        
        try:
            result = await self.trader.buy(address, buy_amount)
            
            if result.success:
                logger.success(f"✅ 狙击成功! TX: {result.tx_signature}")
                
                # 记录持仓
                self.positions[address] = {
                    'symbol': symbol,
                    'buy_price': result.price,
                    'amount': result.output_amount,
                    'sol_spent': buy_amount,
                    'timestamp': datetime.now().isoformat()
                }
                
                # 发送成功通知
                if self.notifier:
                    await self.notifier.notify_buy(
                        symbol=symbol,
                        amount_sol=buy_amount,
                        token_amount=result.output_amount,
                        tx=result.tx_signature or "N/A"
                    )
            else:
                logger.error(f"❌ 狙击失败: {result.error}")
                if self.notifier:
                    await self.notifier.notify_error(f"狙击 {symbol} 失败: {result.error}")
                    
        except Exception as e:
            logger.error(f"狙击执行错误: {e}")
            
    async def handle_pump_alert(self, source: str, data: dict):
        """处理 Pump 报警"""
        token = data.get('token', '???')
        reason = data.get('reason', '')
        
        logger.warning(f"🚨 PUMP 报警 from {source}: {token}")
        logger.info(f"   原因: {reason}")
        
        if self.notifier:
            await self.notifier.send_message(f"🚨 *PUMP 报警*\n\n来源: {source}\n代币: {token}\n原因: {reason}")

# ============================================
# 主程序
# ============================================

async def main():
    logger.info("="*50)
    logger.info("🎯 洛杉矶 - 全球信号接收器 + 狙击机器人")
    logger.info("="*50)
    
    # 加载配置
    config_path = os.path.expanduser('~/solana-sniper-bot/config/config.yaml')
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info("✅ 加载 config.yaml 成功")
    else:
        config = {'telegram': {'enabled': False}}
        logger.warning("⚠️ 未找到 config.yaml")
    
    receiver = GlobalReceiver(config)
    
    try:
        await receiver.start()
    except KeyboardInterrupt:
        logger.info("停止接收器...")

if __name__ == "__main__":
    asyncio.run(main())
