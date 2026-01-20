# 全球 Redis 网状网络安装指南 (Global Redis Mesh Setup)

这个文档教你如何搭建 Master-Slave（虽然我们这里其实是 Pub/Sub 模式）的全球低延迟网络。

## 1. 核心架构原理
- **大脑 (Master)**: 位于德国 (Germany) 或 网络中心。安装 Redis Server。
- **眼睛 (Publishers)**: 位于 香港 (HK) / 大阪 (JP)。只负责 `publish` 消息。
- **手 (Subscribers)**: 位于 洛杉矶 (LA) 或 本地电脑。只负责 `subscribe` 监听。

---

## 2. 德国 Master 节点配置 (大脑)

SSH 登录到你的德国 VPS，执行以下命令：

### 安装 Redis
```bash
sudo apt update
sudo apt install redis-server -y
```

### 修改配置 (关键一步)
默认 Redis 只允许本机连，我们需要开启公网访问，但必须加密码！

```bash
sudo nano /etc/redis/redis.conf
```

1. **允许远程连接**:
   找到 `bind 127.0.0.1 ::1`
   修改为 `bind 0.0.0.0`

2. **设置强密码**:
   找到 `# requirepass foobared`
   去掉注释，改为：
   `requirepass YourSuperSecretGlobalPassword2026!`

3. **保护模式 (可选)**:
   确保 `protected-mode yes` (有密码的情况下 yes 也没事，只要 bind 改了) 或者改为 `no` 如果遇到连接问题（不推荐，建议用密码+白名单）。

### 重启并设置防火墙 (安全防护)
不要让全世界都能扫你的端口！只允许你的其他节点 IP。

```bash
# 重启 Redis
sudo systemctl restart redis-server

# (推荐) 仅允许特定IP访问 (把 x.x.x.x 换成你香港/大阪/洛杉矶的IP)
# sudo ufw allow from x.x.x.x to any port 6379

# (最简单/不安全) 允许所有IP (测试用)
sudo ufw allow 6379
```

---

## 3. 客户端节点配置 (香港/日本/洛杉矶)

在 `solana-global-nodes/global_mesh` 目录下：

1. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

2. **修改配置**:
   打开 `config.yaml`，填入德国 Master 的公网 IP。
   ```yaml
   redis:
     host: "123.45.67.89"  # <--- 填入德国IP
   ```

3. **运行**:
   - 如果是 **香港/日本** (监听行情):
     ```bash
     python publisher.py
     ```
   - 如果是 **洛杉矶/本地** (接收报警):
     ```bash
     python subscriber.py
     ```

## 4. 测试
在本地运行 `subscriber.py`，然后在另一个终端运行 `publisher.py`。你应该能看到毫秒级的消息同步！

---

## 5. ⚠️ IPv6 + WARP 特殊情况

如果你的德国节点是 **纯 IPv6**，并且用 **Cloudflare WARP** 获取 IPv4 出口，那你会遇到问题：

> WARP 只提供 **出站 IPv4**，不提供 **入站**。其他节点无法直接连到德国的 Redis。

### 解决方案 A: 换一个节点当 Master (推荐)

把有 **公网 IPv4** 的节点（比如洛杉矶）作为 Redis Master。

```
[香港] --IPv4--> [洛杉矶 Redis Master] <--IPv4-- [德国 via WARP]
                        |
                      [Bot]
```

修改 `config.yaml` 的 `host` 为洛杉矶的 IP 即可。

### 解决方案 B: 使用 FRP 内网穿透

如果必须用德国当大脑，可以用 [frp](https://github.com/fatedier/frp) 做反向代理：

1. 在有 IPv4 的服务器 (如洛杉矶) 运行 `frps` (服务端)
2. 在德国运行 `frpc` (客户端)，把本地 6379 端口暴露出去
3. 其他节点连接洛杉矶的 frp 端口，流量会自动转发到德国

**frpc.ini 示例 (德国节点):**
```ini
[common]
server_addr = LA_SERVER_IP
server_port = 7000

[redis]
type = tcp
local_ip = 127.0.0.1
local_port = 6379
remote_port = 6379
```

### 解决方案 C: ZeroTier 组建虚拟内网

使用 [ZeroTier](https://www.zerotier.com/) 把所有节点加入同一个虚拟局域网，然后用内网 IP 通信，完全绕过公网 IPv4/IPv6 问题。
