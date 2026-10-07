#!/usr/bin/env python3
"""每天更新本地天气到 Letta 的 human memory block。

城市：从 companion/config.json 的 "city" 字段读取（必填，未填写则退出），
agent id 自动从 letta-server/AGENT_ID.txt 读取。

设置 Windows 任务计划每天运行一次即可实现"她每天感知天气"：
  程序: <部署根>/letta-server/venv/Scripts/python.exe
  参数: <部署根>/update_weather.py
"""
import json
import os
import sys
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))  # 部署根目录（仓库根）

# 城市：必填，从 config.json 的 city 字段读取（不提供默认值，避免写入错误位置）
city = ""
try:
    cfg = json.load(open(os.path.join(ROOT, "companion", "config.json"), encoding="utf-8"))
    city = (cfg.get("city") or "").strip()
except Exception:
    pass
if not city or city.startswith("在这里填"):
    sys.exit("请在 companion/config.json 的 city 字段填写你所在的城市后重试")

# agent id：从 AGENT_ID.txt 自动读取
AID = open(os.path.join(ROOT, "letta-server", "AGENT_ID.txt"), encoding="utf-8").read().strip()
BASE = "http://127.0.0.1:8283"

# 获取天气（wttr.in 无需 key）
try:
    r = requests.get(f"https://wttr.in/{city}?format=j1", timeout=10)
    d = r.json()
    today = d["weather"][0]
    desc = today["hourly"][4]["weatherDesc"][0]["value"]
    mint = today["mintempC"]
    maxt = today["maxtempC"]
    humidity = today["hourly"][4]["humidity"]
    date = today["date"]
    weather_text = f"{city}今天({date})：{desc}，{mint}~{maxt}°C，湿度{humidity}%"
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
