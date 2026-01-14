#!/usr/bin/env python3
"""
🐕 Arb Watchdog - CEX/DEX 价差监控器
监控 Binance vs Solana DEX 的 SOL 价格差异

架构:
- 香港节点: 查询 Binance (1.6ms 延迟)
- 洛杉矶节点: 查询 Solana DEX (1.4ms 延迟) 
- 莱比锡节点: 对比分析 + 报警

Usage: python3 scripts/arb_watchdog.py
"""

import time
import json
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional, Tuple

# =================== 配置区域 ===================
# 监控配置
CHECK_INTERVAL = 0.5      # 检查间隔 (秒)
ALERT_THRESHOLD = 1.0     # 报警阈值 (百分比)
SYMBOL = "SOL"            # 监控币种

# Telegram 配置 (可选)
TELEGRAM_ENABLED = False          # 设为 True 启用 Telegram 通知
TELEGRAM_BOT_TOKEN = ""           # 你的 Bot Token
TELEGRAM_CHAT_ID = ""             # 你的 Chat ID

# API 端点
BINANCE_API = "https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT"
JUPITER_API = "https://price.jup.ag/v6/price?ids=SOL"  # Jupiter 聚合器 (更可靠)
# ================================================

def get_binance_price() -> Optional[float]:
    """
    从 Binance 获取 SOL/USDT 价格 (CEX)
    最佳运行位置: 🇭🇰 香港 (1.6ms)
    """
    try:
        req = urllib.request.Request(BINANCE_API, headers={'User-Agent': 'ArbWatchdog/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return float(data['price'])
    except Exception as e:
        print(f"⚠️ Binance API Error: {e}")
        return None

def get_dex_price() -> Optional[float]:
    """
    从 Solana DEX (Jupiter 聚合器) 获取 SOL 价格
    最佳运行位置: 🇺🇸 洛杉矶 (1.4ms)
    """
    try:
        req = urllib.request.Request(JUPITER_API, headers={'User-Agent': 'ArbWatchdog/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return float(data['data']['SOL']['price'])
    except Exception as e:
        print(f"⚠️ DEX API Error: {e}")
        return None

def calculate_spread(cex_price: float, dex_price: float) -> Tuple[float, str]:
    """
    计算价差百分比
    返回: (价差百分比, 套利方向)
    """
    spread_pct = ((dex_price - cex_price) / cex_price) * 100
    
    if spread_pct > 0:
        direction = "CEX → DEX"  # DEX 价格高，在 CEX 买入后去 DEX 卖出
    else:
        direction = "DEX → CEX"  # CEX 价格高，在 DEX 买入后去 CEX 卖出
    
    return spread_pct, direction

def send_telegram_alert(message: str):
    """发送 Telegram 通知"""
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req, timeout=10)
        print("📱 Telegram alert sent!")
    except Exception as e:
        print(f"⚠️ Telegram Error: {e}")

def print_header():
    """打印监控头部"""
    print("\n" + "="*70)
    print(" 🐕 ARB WATCHDOG - CEX/DEX Price Monitor")
    print(f" 📊 Symbol: {SYMBOL}/USDT")
    print(f" ⏱️ Interval: {CHECK_INTERVAL}s | 🚨 Alert Threshold: {ALERT_THRESHOLD}%")
    print(f" 📱 Telegram: {'Enabled' if TELEGRAM_ENABLED else 'Disabled'}")
    print("="*70)
    print(f"{'TIME':<12} | {'BINANCE':<12} | {'DEX':<12} | {'SPREAD':<10} | {'STATUS'}")
    print("-"*70)

def run_watchdog():
    """运行监控主循环"""
    print_header()
    alert_cooldown = 0
    
    while True:
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 获取价格
            binance_price = get_binance_price()
            dex_price = get_dex_price()
            
            if binance_price and dex_price:
                spread_pct, direction = calculate_spread(binance_price, dex_price)
                abs_spread = abs(spread_pct)
                
                # 状态判定
                if abs_spread >= ALERT_THRESHOLD:
                    status = f"🚨 ARB! {direction}"
                    
                    # 发送报警 (有冷却时间避免刷屏)
                    if alert_cooldown <= 0:
                        alert_msg = (
                            f"🐕 <b>ARB ALERT!</b>\n\n"
                            f"💰 Spread: <b>{abs_spread:.3f}%</b>\n"
                            f"📈 Binance: ${binance_price:.4f}\n"
                            f"📊 DEX: ${dex_price:.4f}\n"
                            f"➡️ Direction: {direction}\n"
                            f"⏰ Time: {timestamp}"
                        )
                        send_telegram_alert(alert_msg)
                        alert_cooldown = 60  # 60秒冷却
                elif abs_spread >= ALERT_THRESHOLD * 0.5:
                    status = "⚠️ WATCHING"
                else:
                    status = "✅ NORMAL"
                
                # 根据价差显示颜色标记
                spread_display = f"{spread_pct:+.3f}%"
                
                print(f"{timestamp:<12} | ${binance_price:<10.4f} | ${dex_price:<10.4f} | {spread_display:<10} | {status}")
            else:
                print(f"{timestamp:<12} | {'ERROR':<12} | {'ERROR':<12} | {'N/A':<10} | ⚠️ API ISSUE")
            
            # 冷却倒计时
            if alert_cooldown > 0:
                alert_cooldown -= CHECK_INTERVAL
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Watchdog stopped by user.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    print("🐕 Initializing Arb Watchdog...")
    print("   Press Ctrl+C to stop\n")
    run_watchdog()
