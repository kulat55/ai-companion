# -*- coding: utf-8 -*-
# 兼容 DeepSeek 2026 新模型名（deepseek-flash / deepseek-v4-pro），否则 Letta 0.16.8 会因
# 查不到上下文窗口而在 provider refresh 时把它们过滤掉，导致模型列表为空。
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # 部署根目录（仓库根）
p = str(ROOT / "letta-server" / "venv" / "Lib" / "site-packages" / "letta" / "schemas" / "providers" / "deepseek.py")
s = open(p, encoding="utf-8").read()
old = '''        if model_name == "deepseek-reasoner":
            return 128000
        elif model_name == "deepseek-chat":
            return 128000
        else:
            return None'''
new = '''        _known = {
            "deepseek-reasoner", "deepseek-chat",
            "deepseek-v4-pro", "deepseek-flash",
        }
        return 128000 if model_name in _known else None'''
if new in s:
    print("already patched")
elif old in s:
    open(p, "w", encoding="utf-8").write(s.replace(old, new))
    print("patched deepseek context-window map")
else:
    raise SystemExit("target block not found, source layout changed")
