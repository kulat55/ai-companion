# -*- coding: utf-8 -*-
# 用 OpenAI 兼容方式接入 DeepSeek（标准 function calling + BYOK 密钥注入）。
import json, urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8283"
NAME = "deepseek-api"
DS_BASE = "https://api.deepseek.com/v1"
key = open(Path(__file__).resolve().parents[1] / "companion" / "deepseek_key.txt").read().strip()

def http(method, path, body=None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else None

provs = http("GET", "/v1/providers/")
ex = next((p for p in provs if p["name"] == NAME), None)
if ex:
    pid = ex["id"]
    http("PATCH", f"/v1/providers/{pid}", {"api_key": key, "base_url": DS_BASE})
    print("updated provider:", pid)
else:
    p = http("POST", "/v1/providers/",
             {"name": NAME, "provider_type": "openai", "api_key": key, "base_url": DS_BASE})
    pid = p["id"]
    print("created provider:", pid)

# 再显式刷新一次模型
try:
    http("PATCH", f"/v1/providers/{pid}/refresh")
except Exception as e:
    print("refresh note:", repr(e)[:160])

print("\n--- 注册出的模型 ---")
for m in http("GET", "/v1/models/"):
    h = m.get("handle", "")
    if h and h.startswith(NAME + "/"):
        print(h, "| endpoint:", m.get("model_endpoint_type"),
              "| ctx:", m.get("context_window"), "| endpoint_url:", m.get("model_endpoint"))
