# -*- coding: utf-8 -*-
"""切换主动消息总开关：python set_flag.py on|off"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(BASE, "config.json")
cfg = json.load(open(CFG, "r", encoding="utf-8"))
cfg["enabled"] = (sys.argv[1].lower() == "on")
json.dump(cfg, open(CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("主动消息已", "开启" if cfg["enabled"] else "关闭")
