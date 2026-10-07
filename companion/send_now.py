# -*- coding: utf-8 -*-
"""立即让AI 伴侣生成一条主动消息。
用法：
  python send_now.py          # 只生成并打印，不发 QQ（NapCat 没配好时用它验证）
  python send_now.py --send   # 生成并真的通过 NapCat 发给 config.target_qq
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from proactive_sender import load_cfg, letta_say, napcat_send, log  # noqa

cfg = load_cfg()
text = letta_say(cfg)
print("=" * 50)
print("AI 伴侣想说：", text)
print("=" * 50)
if "--send" in sys.argv:
    ok, info = napcat_send(cfg, text)
    print("发送结果：", "成功" if ok else "失败", info)
else:
    print("（仅预览，未发送。加 --send 才会真发 QQ）")
