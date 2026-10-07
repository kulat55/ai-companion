#!/usr/bin/env python3
"""AI Companion 全面诊断测试脚本"""
import requests, time, sys, os, json, subprocess, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent  # 部署根目录（仓库根）

PASS = 0; FAIL = 0; WARN = 0
def ok(name, msg=""):
    global PASS; PASS += 1; print(f"  [PASS] {name} {msg}")
def fail(name, msg=""):
    global FAIL; FAIL += 1; print(f"  [FAIL] {name} {msg}")
def warn(name, msg=""):
    global WARN; WARN += 1; print(f"  [WARN] {name} {msg}")

def test_port(name, port, timeout=2):
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", port)); s.close(); return True
    except: return False

print("=" * 60)
print("AI Companion 全面诊断")
print("=" * 60)

# 1. 端口检测
print("\n--- 1. 服务端口 ---")
pg_port = 55432
try:
    pf = ROOT / "pgdata" / "PORT"
    if pf.is_file():
        pg_port = int(pf.read_text().strip())
except Exception:
    pass
ports = {"PostgreSQL": pg_port, "Letta": 8283, "VTuber": 12393}
for name, port in ports.items():
    if test_port(name, port): ok(f"{name} ({port})")
    else: fail(f"{name} ({port})", "端口未监听")
print("  [注] Ollama 11434 为可选（仅本地模型需要），见第 3 节")

# 2. Letta API
print("\n--- 2. Letta API ---")
try:
    r = requests.get("http://127.0.0.1:8283/v1/agents/", timeout=5)
    if r.status_code == 200:
        agents = r.json()
        ok(f"Letta agents API", f"({len(agents)} 个 agent)")
        if agents:
            # 跳过 Letta 自带的 sleeptime 系统 agent，测主 agent
            main = [a for a in agents if "sleeptime" not in a.get("name", "")]
            aid = (main[0] if main else agents[0])["id"]
            # 获取 agent 详情
            r2 = requests.get(f"http://127.0.0.1:8283/v1/agents/{aid}", timeout=5)
            if r2.status_code == 200:
                ag = r2.json()
                model = ag.get("llm_config", {}).get("model", "?")
                endpoint = ag.get("llm_config", {}).get("model_endpoint", "?")
                ok(f"Agent 模型", f"{model} @ {endpoint}")
                # 测试发消息
                print("  正在测试发消息（本地模型可能需20-60秒）...")
                t0 = time.time()
                r3 = requests.post(
                    f"http://127.0.0.1:8283/v1/agents/{aid}/messages",
                    json={"messages": [{"role": "user", "content": "测试，请回复一个字：好"}]},
                    timeout=120
                )
                dt = time.time() - t0
                if r3.status_code == 200:
                    msgs = r3.json().get("messages", [])
                    reply = ""
                    for m in reversed(msgs):
                        if m.get("message_type") == "assistant_message":
                            c = m.get("content", "")
                            if isinstance(c, list): c = "".join(x.get("text","") for x in c if x)
                            if c.strip(): reply = c; break
                    if reply.strip():
                        ok(f"消息往返", f"耗时{dt:.1f}s，回复：{reply[:50]}")
                    else:
                        fail("消息往返", "空回复！模型可能又上下文不够")
                else:
                    fail("发消息", f"HTTP {r3.status_code}: {r3.text[:200]}")
            else:
                fail("Agent 详情", f"HTTP {r2.status_code}")
    else:
        fail("Letta agents API", f"HTTP {r.status_code}")
except Exception as e:
    fail("Letta API", str(e))

# 3. Ollama 状态
print("\n--- 3. Ollama ---")
try:
    r = requests.get("http://127.0.0.1:11434/api/ps", timeout=5)
    d = r.json()
    if d.get("models"):
        for m in d["models"]:
            vram = m.get("size_vram", 0) // 1048576
            ctx = m.get("context_length", "?")
            ok(f"模型已加载", f"{m['name']} VRAM={vram}MB ctx={ctx}")
    else:
        warn("Ollama", "没有模型加载（会自动加载）")
except Exception as e:
    fail("Ollama", str(e))

# 4. TTS 测试
print("\n--- 4. TTS (edge-tts) ---")
try:
    import edge_tts, asyncio
    async def tts_test():
        c = edge_tts.Communicate("测试语音", "zh-CN-XiaoxiaoNeural")
        out = str(ROOT / "test_tts_check.mp3")
        await c.save(out)
        return os.path.getsize(out)
    size = asyncio.run(tts_test())
    if size > 1000: ok(f"edge-tts", f"生成 {size} 字节音频")
    else: fail("edge-tts", f"文件太小 ({size}B)")
except Exception as e:
    fail("edge-tts", str(e))

# 5. 前端页面
print("\n--- 5. 前端页面 ---")
try:
    r = requests.get("http://127.0.0.1:12393/", timeout=5)
    if r.status_code == 200 and len(r.text) > 1000:
        ok("前端 HTML", f"{len(r.text)} 字节")
        # 检查注入是否存在
        checks = {
            "管理面板": "admin-fab",
            "心情状态": "p-mood",
            "时间问候": "p-greet",
            "模型切换": "btn-switch",
        }
        for label, key in checks.items():
            if key in r.text: ok(f"注入-{label}")
            else: warn(f"注入-{label}", "未找到")
        # 检查括号平衡
        opens = r.text.count("{"); closes = r.text.count("}")
        if opens == closes: ok("大括号平衡", f"({opens})")
        else: fail("大括号不平衡", f"open={opens} close={closes}")
    else:
        fail("前端 HTML", f"status={r.status_code}")
except Exception as e:
    fail("前端页面", str(e))

# 6. WebSocket 连接测试
print("\n--- 6. WebSocket ---")
try:
    import websocket
    ws = websocket.create_connection("ws://127.0.0.1:12393/client-ws", timeout=5)
    ok("WebSocket 连接", "已建立")
    ws.close()
except ImportError:
    warn("WebSocket", "websocket-client 未安装，跳过")
except Exception as e:
    fail("WebSocket", str(e))

# 汇总
print("\n" + "=" * 60)
print(f"结果: {PASS} 通过 / {FAIL} 失败 / {WARN} 警告")
print("=" * 60)
sys.exit(1 if FAIL else 0)
