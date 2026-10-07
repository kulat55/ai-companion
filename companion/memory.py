# -*- coding: utf-8 -*-
"""
AI 伴侣记忆管理工具（记忆全部存在你本机，可随时查看 / 修改 / 导出）
用法（在本目录用 Letta 的 python 运行）：
  python memory.py show                查看她的“核心记忆”（persona 人格 + human 关于你）
  python memory.py edit human          用记事本打开“关于你”的记忆，改完保存关闭即生效
  python memory.py edit persona        用记事本打开“人格设定”，可视化修改她的性格
  python memory.py append human 文本    往“关于你”里追加一条（也可传一个 .txt 文件路径）
  python memory.py set human 文本/文件  整体覆盖“关于你”
  python memory.py history 20          查看最近 20 条对话记录
  python memory.py search 关键词       在历史对话里检索
  python memory.py passages           查看她的长期(向量)记忆条目
  python memory.py export             把全部记忆导出成 Markdown 备份到 backups 目录
"""
import json
import os
import subprocess
import sys
from datetime import datetime

from letta_client import Letta

BASE = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "http://127.0.0.1:8283"
AGENT_ID_FILE = r"D:\AICompanion\letta-server\AGENT_ID.txt"
BACKUP_DIR = os.path.join(BASE, "backups")


def client_and_agent():
    aid = open(AGENT_ID_FILE, encoding="utf-8").read().strip()
    return Letta(base_url=BASE_URL), aid


def get_blocks(c, aid):
    return {b.label: b for b in c.agents.blocks.list(agent_id=aid)}


def arg_text(arg):
    """命令行参数：若是存在的文件则读文件，否则当字面文本"""
    if arg and os.path.isfile(arg):
        return open(arg, encoding="utf-8").read().strip()
    return arg


def cmd_show(c, aid):
    for label, b in get_blocks(c, aid).items():
        print("=" * 60)
        print(f"【{label}】(上限 {b.limit} 字，当前 {len(b.value or '')} 字)")
        print("-" * 60)
        print(b.value)
    print("=" * 60)


def cmd_set(c, aid, label, text, append=False):
    blocks = get_blocks(c, aid)
    if label not in blocks:
        raise SystemExit(f"没有记忆块 {label}，现有：{list(blocks)}")
    old = blocks[label].value or ""
    new = (old + "\n" + text) if append else text
    c.agents.blocks.update(agent_id=aid, block_id=blocks[label].id, value=new)
    print(f"已{'追加' if append else '更新'}【{label}】，现共 {len(new)} 字")


def cmd_edit(c, aid, label):
    blocks = get_blocks(c, aid)
    if label not in blocks:
        raise SystemExit(f"没有记忆块 {label}，现有：{list(blocks)}")
    tmp = os.path.join(BASE, f"_edit_{label}.txt")
    open(tmp, "w", encoding="utf-8").write(blocks[label].value or "")
    print("正在打开记事本，修改后请【保存并关闭记事本】，程序会自动写回她的记忆…")
    subprocess.run(["notepad.exe", tmp])
    new = open(tmp, encoding="utf-8").read().strip()
    c.agents.blocks.update(agent_id=aid, block_id=blocks[label].id, value=new)
    try:
        os.remove(tmp)
    except OSError:
        pass
    print(f"【{label}】已保存，共 {len(new)} 字，下一句对话即生效。")


def _msg_text(m):
    c = getattr(m, "content", "")
    if isinstance(c, list):
        return " ".join(getattr(x, "text", "") or "" for x in c)
    return c or ""


def cmd_history(c, aid, n=20):
    msgs = c.agents.messages.list(agent_id=aid, limit=int(n))
    for m in msgs:
        mt = getattr(m, "message_type", "")
        if mt not in ("user_message", "assistant_message"):
            continue
        who = "大人" if mt == "user_message" else "AI 伴侣"
        print(f"[{getattr(m,'date','')}] {who}：{_msg_text(m)}")


def cmd_search(c, aid, kw):
    msgs = c.agents.messages.list(agent_id=aid, limit=200)
    hit = 0
    for m in msgs:
        if getattr(m, "message_type", "") not in ("user_message", "assistant_message"):
            continue
        t = _msg_text(m)
        if kw in t:
            who = "大人" if m.message_type == "user_message" else "AI 伴侣"
            print(f"[{getattr(m,'date','')}] {who}：{t}")
            hit += 1
    print(f"——命中 {hit} 条——")


def cmd_passages(c, aid):
    try:
        ps = c.agents.passages.list(agent_id=aid, limit=100)
        for p in ps:
            print(f"- ({getattr(p,'created_at','')}) {getattr(p,'text','')}")
    except Exception as e:
        print("读取长期记忆失败：", e)


def cmd_export(c, aid):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(BACKUP_DIR, f"albedo_memory_{stamp}.md")
    lines = [f"# AI 伴侣记忆备份 {stamp}", ""]
    for label, b in get_blocks(c, aid).items():
        lines += [f"## 核心记忆·{label}", b.value or "", ""]
    lines += ["## 对话记录", ""]
    for m in c.agents.messages.list(agent_id=aid, limit=10000):
        if getattr(m, "message_type", "") not in ("user_message", "assistant_message"):
            continue
        who = "大人" if m.message_type == "user_message" else "AI 伴侣"
        lines.append(f"- [{getattr(m,'date','')}] {who}：{_msg_text(m)}")
    open(out, "w", encoding="utf-8").write("\n".join(lines))
    print("已导出：", out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    c, aid = client_and_agent()
    cmd = sys.argv[1]
    if cmd == "show":
        cmd_show(c, aid)
    elif cmd == "edit":
        cmd_edit(c, aid, sys.argv[2])
    elif cmd == "set":
        cmd_set(c, aid, sys.argv[2], arg_text(" ".join(sys.argv[3:])), False)
    elif cmd == "append":
        cmd_set(c, aid, sys.argv[2], arg_text(" ".join(sys.argv[3:])), True)
    elif cmd == "history":
        cmd_history(c, aid, sys.argv[2] if len(sys.argv) > 2 else 20)
    elif cmd == "search":
        cmd_search(c, aid, " ".join(sys.argv[2:]))
    elif cmd == "passages":
        cmd_passages(c, aid)
    elif cmd == "export":
        cmd_export(c, aid)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
