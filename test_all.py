#!/usr/bin/env python3
"""AI Companion 全面功能测试 - 覆盖所有核心功能"""
import requests, time, sys, os, json, socket, asyncio

BASE = "http://127.0.0.1:8283"
VTUBER = "http://127.0.0.1:12393"
OLLAMA = "http://127.0.0.1:11434"
ROOT = os.path.dirname(os.path.abspath(__file__))  # 部署根目录（仓库根）

results = []
def test(name, ok, detail=""):
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name} {detail}")

def port_open(port, timeout=2):
    s = socket.socket(); s.settimeout(timeout)
    try: s.connect(("127.0.0.1", port)); s.close(); return True
    except: return False

print("=" * 60)
print("AI Companion 全面功能测试")
print("=" * 60)

# === 1. 服务端口 ===
print("\n--- 1. 服务端口 ---")
test("PostgreSQL 55432", port_open(55432))
test("Letta 8283", port_open(8283))
test("VTuber 12393", port_open(12393))
test("Ollama 11434", port_open(11434))

# === 2. Letta Agent 管理 ===
print("\n--- 2. Letta Agent ---")
try:
    r = requests.get(f"{BASE}/v1/agents/", timeout=5)
    agents = r.json()
    test("获取 agent 列表", len(agents) >= 1, f"({len(agents)} 个)")
    main = [a for a in agents if "sleeptime" not in a.get("name","")]
    if main:
        aid = main[0]["id"]
        test("找到主 agent", True, main[0].get("name",""))
        # 获取详情
        r2 = requests.get(f"{BASE}/v1/agents/{aid}", timeout=5)
        ag = r2.json()
        model = ag["llm_config"]["model"]
        ep = ag["llm_config"]["model_endpoint"]
        test("当前模型", True, f"{model} @ {ep}")
    else:
        test("找到主 agent", False, "只有 sleeptime agent")
        aid = agents[0]["id"]
except Exception as e:
    test("Letta API", False, str(e))
    aid = None

# === 3. 核心记忆读写 ===
print("\n--- 3. 核心记忆 ---")
if aid:
    try:
        r = requests.get(f"{BASE}/v1/agents/{aid}/memory/blocks", timeout=5)
        blocks = r.json()
        if isinstance(blocks, dict): blocks = blocks.get("blocks", list(blocks.values()))
        test("获取记忆块", len(blocks) >= 1, f"({len(blocks)} 块)")
        for b in blocks:
            if isinstance(b, dict):
                v = b.get("value","")
                test(f"记忆-{b.get('label','?')}", len(v) > 0, f"({len(v)} 字)")
    except Exception as e:
        test("记忆读取", False, str(e))

# === 4. 对话历史 ===
print("\n--- 4. 对话历史 ---")
if aid:
    try:
        r = requests.get(f"{BASE}/v1/agents/{aid}/messages?limit=10", timeout=5)
        msgs = r.json()
        test("获取历史消息", isinstance(msgs, list), f"({len(msgs)} 条)")
        asst = [m for m in msgs if m.get("message_type")=="assistant_message"]
        test("有 assistant 回复", len(asst) > 0, f"({len(asst)} 条)")
    except Exception as e:
        test("历史读取", False, str(e))

# === 5. 模型切换（往返） ===
print("\n--- 5. 模型切换 ---")
if aid:
    # 切到 flash
    try:
        r = requests.patch(f"{BASE}/v1/agents/{aid}", json={"model":"openai-proxy/deepseek-flash"}, timeout=10)
        test("切到 Flash", r.status_code==200, r.json()["llm_config"]["model"])
    except Exception as e:
        test("切到 Flash", False, str(e))

# === 6. 对话往返（实际发消息） ===
print("\n--- 6. 对话往返（发'你好'） ---")
if aid:
    try:
        t0 = time.time()
        r = requests.post(f"{BASE}/v1/agents/{aid}/messages",
            json={"messages":[{"role":"user","content":"你好"}]}, timeout=120)
        dt = time.time() - t0
        if r.status_code == 200:
            msgs = r.json().get("messages",[])
            reply = ""
            for m in reversed(msgs):
                if m.get("message_type")=="assistant_message":
                    c = m.get("content","")
                    if isinstance(c, list): c = "".join(x.get("text","") for x in c if x)
                    if c.strip(): reply = c; break
                elif m.get("message_type")=="tool_call_message" and m.get("tool_call",{}).get("name")=="send_message":
                    import json as _j
                    try: reply = _j.loads(m["tool_call"]["arguments"]).get("message","")
                    except: pass
            test("收到回复", len(reply) > 0, f"({dt:.1f}s) {reply[:60]}...")
        else:
            test("发消息", False, f"HTTP {r.status_code}")
    except Exception as e:
        test("对话往返", False, str(e))

# === 7. Ollama 状态 ===
print("\n--- 7. Ollama ---")
try:
    r = requests.get(f"{OLLAMA}/api/ps", timeout=3)
    d = r.json()
    if d.get("models"):
        m = d["models"][0]
        test("本地模型已加载", True, f"{m['name']} VRAM={m['size_vram']//1048576}MB")
    else:
        test("本地模型", True, "空闲（未加载，正常）")
except Exception as e:
    test("Ollama", False, str(e))

# === 8. TTS ===
print("\n--- 8. TTS ---")
try:
    import edge_tts, asyncio
    async def tts():
        c = edge_tts.Communicate("测试", "zh-CN-XiaoxiaoNeural")
        await c.save(os.path.join(ROOT, "test_tts2.mp3"))
        return os.path.getsize(os.path.join(ROOT, "test_tts2.mp3"))
    size = asyncio.run(tts())
    test("edge-tts 生成", size > 1000, f"({size}B)")
except Exception as e:
    test("TTS", False, str(e))

# === 9. 前端页面 ===
print("\n--- 9. 前端页面 ---")
try:
    r = requests.get(f"{VTUBER}/", timeout=5)
    html = r.text
    test("页面加载", r.status_code==200 and len(html)>1000, f"({len(html)}B)")
    test("管理面板注入", "admin-fab" in html)
    test("心情状态注入", "p-mood" in html)
    test("问候注入", "p-greet" in html)
    test("一键诊断", "一键诊断" in html)
    test("TTS试听", "试听她的声音" in html)
    test("大括号平衡", html.count("{")==html.count("}"), f"({html.count('{')}/{html.count('}')})")
except Exception as e:
    test("前端", False, str(e))

# === 汇总 ===
print("\n" + "=" * 60)
passed = sum(1 for _,ok,_ in results if ok)
failed = sum(1 for _,ok,_ in results if not ok)
print(f"结果: {passed} 通过 / {failed} 失败 / {len(results)} 总计")
if failed:
    print("\n失败项:")
    for name, ok, detail in results:
        if not ok: print(f"  ❌ {name}: {detail}")
print("=" * 60)
