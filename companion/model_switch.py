# -*- coding: utf-8 -*-
"""
在“DeepSeek 云端（正式）”与“本地 qwen2.5:7b（测试）”之间切换雅儿贝德的大脑。
记忆向量嵌入始终使用本地 bge-m3，不走云端、不花 token、不出本机。

DeepSeek 必须走 OpenAI 兼容供应商（name=deepseek-api，handle 前缀 openai-proxy/），
该通道才会下发记忆工具；旧的 deepseek 专用通道不传工具、无法写记忆，勿用。

用法：
  python model_switch.py deepseek [key] [v4-pro|flash]   # 配置并切到云端（key 默认读 deepseek_key.txt）
  python model_switch.py local                           # 切回本地 qwen2.5:7b（需先开 Ollama）
  python model_switch.py status                          # 查看当前模型与可用模型
"""
import json
import os
import sys
import urllib.request

from letta_client import Letta

BASE = "http://127.0.0.1:8283"
AGENT_ID_FILE = r"D:\AICompanion\letta-server\AGENT_ID.txt"
KEY_FILE = r"D:\AICompanion\companion\deepseek_key.txt"
LOCAL_MODEL = "ollama-local/qwen2.5:7b-albedo"
DS_NAME = "deepseek-api"
DS_BASE = "https://api.deepseek.com/v1"
DS_MODEL = "openai-proxy/deepseek-v4-pro"


def http(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read().decode("utf-8")
        return json.loads(raw) if raw else None


def aid():
    return open(AGENT_ID_FILE, encoding="utf-8").read().strip()


def setup_deepseek(key, variant="v4-pro"):
    providers = http("GET", "/v1/providers/") or []
    existing = next((p for p in providers if p.get("name") == DS_NAME), None)
    if existing:
        pid = existing["id"]
        # PATCH base_url 时必须同时带 api_key，否则 422
        http("PATCH", f"/v1/providers/{pid}",
             {"provider_type": "openai", "base_url": DS_BASE, "api_key": key})
        print("已更新 DeepSeek(OpenAI兼容) 供应商：", pid)
    else:
        p = http("POST", "/v1/providers/",
                 {"name": DS_NAME, "provider_type": "openai",
                  "base_url": DS_BASE, "api_key": key})
        pid = p["id"]
        print("已创建 DeepSeek(OpenAI兼容) 供应商：", pid)
    try:
        http("PATCH", f"/v1/providers/{pid}/refresh")
    except Exception as e:
        print("刷新模型列表时提示：", e)

    handles = [m.handle for m in Letta(base_url=BASE, timeout=60).models.list()]
    cand = [h for h in handles if h.startswith("openai-proxy/")]
    print("OpenAI 兼容通道可用模型：", cand)
    want = "deepseek-flash" if variant == "flash" else "deepseek-v4-pro"
    prefer = [h for h in cand if h.endswith("/" + want)]
    if not prefer:
        prefer = [h for h in cand if h.endswith("/deepseek-v4-pro")] or \
                 [h for h in cand if h.endswith("/deepseek-flash")]
    return (prefer or [DS_MODEL])[0]


def switch(handle):
    c = Letta(base_url=BASE, timeout=60)
    a = c.agents.update(agent_id=aid(), model=handle)
    print("当前对话模型已切换为：", a.model)


def status():
    c = Letta(base_url=BASE, timeout=60)
    a = c.agents.retrieve(agent_id=aid())
    print("当前对话模型：", a.model)
    print("  endpoint：", a.llm_config.model_endpoint,
          "| 类型：", a.llm_config.model_endpoint_type)
    emb = getattr(a, "embedding_config", None)
    print("嵌入模型：", getattr(emb, "embedding_model", emb))
    print("可用对话模型：")
    for m in c.models.list():
        print("  -", m.handle)


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "status":
        status(); return
    mode = sys.argv[1]
    if mode == "local":
        switch(LOCAL_MODEL)
        print("已切回本地模型（请确认 Ollama 已启动且已拉取 qwen2.5:7b）。记忆仍在本机。")
    elif mode == "deepseek":
        key = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].startswith("sk-") else (
            open(KEY_FILE, encoding="utf-8").read().strip() if os.path.isfile(KEY_FILE) else "")
        variant = "flash" if ((len(sys.argv) > 2 and sys.argv[-1] == "flash") or
                              (len(sys.argv) > 3 and sys.argv[3] == "flash")) else "v4-pro"
        if not key.startswith("sk-"):
            raise SystemExit("没有有效 DeepSeek key：作为参数传入，或写入 companion\\deepseek_key.txt")
        handle = setup_deepseek(key, variant)
        switch(handle)
        print("完成：雅儿贝德现在由 DeepSeek(%s) 驱动，记忆仍全部保存在本机。" % variant)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
