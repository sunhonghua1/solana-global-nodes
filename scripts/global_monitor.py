import subprocess
import json
import datetime
import time

# --- 配置区域 ---
# 你的自定义代币地址
TOKEN_MINT = "6F4sJGKuYtzaZ5ENC2DAxnbg4ZhRCwZHuP9QRe4REAFx"

# 全球节点列表 (名称: 钱包地址)
NODES = {
    "🇩🇪 Leipzig (Master)": "AsrvXt3sRmGdqi1ZbxaTX6Q3VqVkVhApvf6WVVe6G9DM",
    "🇺🇸 Los Angeles (Edge)": "F5rqhcShdiQxr6ZgJSEmqzQBvaEFm6zSVwVdFA6y69RW",
    "🇭🇰 Hong Kong (Bot)": "6TqxxtoE4MxYtLbmsXtt7tXr5QCEXCeoPbkoM7JKrrNi",
    "🇯🇵 Osaka (RPC)": "4Qaaemy1m9LvC7H5nqys7s7Cry91KzGRQFyhApWtUigP"
}
# ----------------

def get_sol_balance(pubkey):
    """查询 SOL 余额"""
    if "Pending" in pubkey: return "N/A"
    try:
        result = subprocess.check_output(
            ["solana", "balance", pubkey, "--url", "devnet"], 
            stderr=subprocess.STDOUT
        ).decode("utf-8").strip()
        return result
    except Exception:
        return "Error"

def get_token_balance(pubkey, mint):
    """查询代币余额"""
    if "Pending" in pubkey: return "N/A"
    try:
        # 使用 spl-token balance 命令
        result = subprocess.check_output(
            ["spl-token", "balance", mint, "--owner", pubkey, "--url", "devnet"],
            stderr=subprocess.STDOUT
        ).decode("utf-8").strip()
        # 处理可能的空返回或错误
        if "could not find" in result.lower():
            return "0 (No Account)"
        return result
    except Exception:
        return "0"

def print_dashboard():
    print("\n" + "="*60)
    print(f" 🌍 GLOBAL SOLANA INFRASTRUCTURE MONITOR")
    print(f" 🕒 Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f" 🔑 Token Mint: {TOKEN_MINT[:6]}...{TOKEN_MINT[-4:]}")
    print("="*60)
    
    # 表头
    print(f"{'NODE LOCATION':<25} | {'SOL BALANCE':<15} | {'TOKEN BALANCE':<15}")
    print("-" * 60)
    
    # 遍历查询
    for name, address in NODES.items():
        print(f"Scanning {name}...", end="\r") # 动态加载效果
        sol = get_sol_balance(address)
        token = get_token_balance(address, TOKEN_MINT)
        
        # 简单的状态着色（如果支持）或标记
        status_mark = "✅" if sol != "Error" and sol != "N/A" else "⚠️"
        
        # 打印行
        print(f"{status_mark} {name:<22} | {sol:<15} | {token:<15}")
        time.sleep(0.5) # 防止请求过快被限流

    print("="*60 + "\n")

if __name__ == "__main__":
    print("Initializing Connection to Solana Devnet Cluster...")
    print_dashboard()
