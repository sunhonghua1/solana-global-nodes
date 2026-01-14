#!/usr/bin/env python3
"""
🌍 Global Exchange Latency Tester
测试全球各节点到交易所 API 的响应延迟

Usage: python3 scripts/latency_test.py
"""

import socket
import time
import statistics
from datetime import datetime

# --- 配置区域 ---
# 测试目标 (交易所 API 端点)
ENDPOINTS = {
    "Binance Futures": ("fapi.binance.com", 443),
    "Binance Spot": ("api.binance.com", 443),
    "OKX API": ("www.okx.com", 443),
    "OKX AWS": ("aws.okx.com", 443),
    "Solana Devnet RPC": ("api.devnet.solana.com", 443),
    "Solana Mainnet RPC": ("api.mainnet-beta.solana.com", 443),
}

# 每个端点测试次数
TEST_COUNT = 5

# 节点位置 (自动检测或手动设置)
# 可通过环境变量 NODE_NAME 手动覆盖: export NODE_NAME="🇯🇵 Osaka"
NODE_LOCATIONS = {
    # hostname 匹配
    "srv28836": "🇩🇪 Leipzig",
    "VM-HKG": "🇭🇰 Hong Kong",
}

# 公网 IP 匹配 (用于 AWS 等动态主机名的服务器)
NODE_IPS = {
    "104.28.206.119": "🇺🇸 Los Angeles",
    "56.155.17.251": "🇯🇵 Osaka",
    "205.198.66.34": "🇭🇰 Hong Kong",
}
# ----------------

def get_public_ip():
    """获取服务器公网 IP"""
    import urllib.request
    try:
        return urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf8')
    except:
        return None

def get_node_name():
    """获取当前节点名称"""
    import os
    
    # 1. 先检查环境变量覆盖
    env_name = os.environ.get('NODE_NAME')
    if env_name:
        return env_name
    
    # 2. 检查主机名匹配
    hostname = socket.gethostname().lower()
    for key, name in NODE_LOCATIONS.items():
        if key.lower() in hostname:
            return name
    
    # 3. 检查公网 IP 匹配
    public_ip = get_public_ip()
    if public_ip and public_ip in NODE_IPS:
        return NODE_IPS[public_ip]
    
    # 4. 默认返回主机名
    return f"🖥️ {socket.gethostname()}"

def test_tcp_latency(host, port, count=5):
    """
    测试 TCP 连接延迟 (毫秒)
    返回: (最小, 平均, 最大, 成功率)
    """
    latencies = []
    success = 0
    
    for _ in range(count):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            start = time.perf_counter()
            sock.connect((host, port))
            end = time.perf_counter()
            
            latency_ms = (end - start) * 1000
            latencies.append(latency_ms)
            success += 1
            sock.close()
            
        except Exception:
            pass
        
        time.sleep(0.1)  # 防止过快请求
    
    if not latencies:
        return None, None, None, 0
    
    return (
        min(latencies),
        statistics.mean(latencies),
        max(latencies),
        (success / count) * 100
    )

def get_latency_rating(avg_ms):
    """根据延迟评级"""
    if avg_ms is None:
        return "❌ FAIL"
    elif avg_ms < 50:
        return "🟢 极速"
    elif avg_ms < 100:
        return "🟡 快速"
    elif avg_ms < 200:
        return "🟠 中等"
    else:
        return "🔴 慢速"

def print_heatmap():
    """打印延迟热力图"""
    node_name = get_node_name()
    
    print("\n" + "="*75)
    print(f" 🌐 GLOBAL EXCHANGE LATENCY HEATMAP")
    print(f" 📍 Testing from: {node_name}")
    print(f" 🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("="*75)
    
    # 表头
    print(f"{'ENDPOINT':<25} | {'MIN':<8} | {'AVG':<8} | {'MAX':<8} | {'RATING':<10}")
    print("-" * 75)
    
    results = []
    
    for name, (host, port) in ENDPOINTS.items():
        print(f"Testing {name}...", end="\r")
        
        min_ms, avg_ms, max_ms, success_rate = test_tcp_latency(host, port, TEST_COUNT)
        rating = get_latency_rating(avg_ms)
        
        if avg_ms is not None:
            print(f"{name:<25} | {min_ms:>6.1f}ms | {avg_ms:>6.1f}ms | {max_ms:>6.1f}ms | {rating:<10}")
            results.append((name, avg_ms))
        else:
            print(f"{name:<25} | {'N/A':>8} | {'N/A':>8} | {'N/A':>8} | {rating:<10}")
    
    print("="*75)
    
    # 最佳交易所推荐
    if results:
        # 只看交易所 (排除 Solana RPC)
        exchange_results = [(n, l) for n, l in results if "Solana" not in n]
        if exchange_results:
            best = min(exchange_results, key=lambda x: x[1])
            print(f"\n💡 推荐: 从 {node_name} 连接 {best[0]} 延迟最低 ({best[1]:.1f}ms)")
    
    print()

def print_all_nodes_summary():
    """提示如何在所有节点运行"""
    print("="*75)
    print(" 📊 完整热力图需要在所有节点运行此脚本")
    print("="*75)
    print("""
    在每个节点执行:
    
    🇩🇪 Leipzig:     ssh root@srv28836 'cd ~/solana-global-nodes && python3 scripts/latency_test.py'
    🇺🇸 LA:          ssh root@... 'cd ~/solana-global-nodes && python3 scripts/latency_test.py'
    🇭🇰 Hong Kong:   ssh root@... 'cd ~/solana-global-nodes && python3 scripts/latency_test.py'
    🇯🇵 Osaka:       ssh root@... 'cd ~/solana-global-nodes && python3 scripts/latency_test.py'
    
    然后汇总结果，找出最佳交易节点！
    """)

if __name__ == "__main__":
    print("🚀 Initializing Global Latency Tester...")
    print_heatmap()
    print_all_nodes_summary()
