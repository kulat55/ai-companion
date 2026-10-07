# -*- coding: utf-8 -*-
import json, time, urllib.request

BASE = "http://127.0.0.1:8283"

def req(method, path, body=None, timeout=60):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    for attempt in range(10):
        try:
            with urllib.request.urlopen(r, timeout=timeout) as resp:
                raw = resp.read().decode()
                return resp.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode()
        except Exception as e:
            time.sleep(2)
    return None, "not ready"

st, h = req("GET", "/v1/health/")
print("health:", st)

st, providers = req("GET", "/v1/providers/")
ds = next((p for p in providers if p.get("name") in ("deepseek-api", "deepseek")), None)
print("deepseek provider:", ds["id"] if ds else None)

st, body = req("PATCH", f"/v1/providers/{ds['id']}/refresh")
print("refresh:", st)

st, models = req("GET", "/v1/models/")
print("--- deepseek models registered ---")
for m in models:
    hnd = m.get("handle", "")
    if hnd.startswith("deepseek-api/") or hnd.startswith("deepseek/"):
        print(" ", hnd, "| ctx:", m.get("context_window"), "| endpoint:", m.get("model_endpoint_type"))
