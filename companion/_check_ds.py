# -*- coding: utf-8 -*-
import json, urllib.request

BASE = "http://127.0.0.1:8283"

def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# 找 deepseek provider（本仓库注册名 deepseek-api；兼容旧名 deepseek）
st, providers = req("GET", "/v1/providers/")
ds = next((p for p in providers if p.get("name") in ("deepseek-api", "deepseek")), None)
print("provider:", ds["id"] if ds else None, ds.get("provider_type") if ds else None)

# check
if ds:
    st, body = req("POST", f"/v1/providers/{ds['id']}/check")
    print("check status:", st)
    # 注意：check 响应可能包含 api_key，打印前先剔除敏感字段
    if isinstance(body, dict):
        for k in list(body.keys()):
            if "key" in k.lower() or "secret" in k.lower():
                body[k] = "***"
    print("check body:", json.dumps(body, ensure_ascii=False)[:1200])
    # refresh
    st, body = req("PATCH", f"/v1/providers/{ds['id']}/refresh")
    print("refresh:", st, json.dumps(body, ensure_ascii=False)[:400])

# 再列模型
st, models = req("GET", "/v1/models/")
for m in models:
    print("MODEL:", m.get("handle"))
