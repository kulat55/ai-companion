#!/usr/bin/env python3
"""每天更新苏州天气到 Letta 的 human memory block"""
import requests, sys, os

AID = "agent-3e6c3a72-c372-4f16-ac83-08143c0ebe63"
BASE = "http://127.0.0.1:8283"

# 获取苏州天气
try:
    r = requests.get("https://wttr.in/Suzhou?format=j1", timeout=10)
    d = r.json()
    today = d["weather"][0]
    desc = today["hourly"][4]["weatherDesc"][0]["value"]
    temp = today["avgtempC"]
    mint = today["mintempC"]
    maxt = today["maxtempC"]
    humidity = today["hourly"][4]["humidity"]
    date = today["date"]
    weather_text = f"苏州今天({date})：{desc}，{mint}~{maxt}°C，湿度{humidity}%"
except Exception as e:
    weather_text = f"天气查询失败: {e}"

print(weather_text)

# 读取当前 human block
r = requests.get(f"{BASE}/v1/agents/{AID}/core-memory/blocks", timeout=5)
blocks = r.json()
human = [b for b in blocks if b["label"] == "human"][0]
current = human["value"]

# 移除旧的天气行
lines = [l for l in current.split("\n") if not l.startswith("【当前天气】")]
# 加新天气
lines.append(f"\n【当前天气】{weather_text}")

# 写回
requests.patch(
    f"{BASE}/v1/agents/{AID}/core-memory/blocks/human",
    json={"value": "\n".join(lines)},
    timeout=10
)
print("weather updated to memory")

