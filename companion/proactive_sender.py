# -*- coding: utf-8 -*-
"""
AI 伴侣 · QQ 主动消息守护进程
- 按 config.json 的 daily_times（带随机偏移）定时唤醒
- 调本地 Letta，让AI 伴侣基于长期记忆自己生成一句话
- 通过本机 NapCat(OneBot HTTP) 私聊发给 target_qq
- 开关 / 时间 / 接收号全部热更新：直接改 config.json 即可，无需重启
启动：  <部署根>\letta-server\venv\Scripts\python.exe proactive_sender.py
"""
import json
import os
import random
import sys
import time
import urllib.request
from datetime import datetime, timedelta, date

BASE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(BASE, "config.json")
STATE = os.path.join(BASE, "state.json")
LOG = os.path.join(BASE, "proactive.log")

WEEK_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_cfg():
    with open(CFG, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if os.path.isfile(STATE):
        try:
            return json.load(open(STATE, "r", encoding="utf-8"))
        except Exception:
            pass
    return {"date": "", "sent": [], "last_send_ts": 0.0}


def save_state(st):
    json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def in_quiet(now, quiet):
    """quiet=[start,end]，支持跨零点"""
    try:
        sh, sm = map(int, quiet[0].split(":"))
        eh, em = map(int, quiet[1].split(":"))
        cur = now.hour * 60 + now.minute
        s, e = sh * 60 + sm, eh * 60 + em
        if s <= e:
            return s <= cur < e
        return cur >= s or cur < e  # 跨零点
    except Exception:
        return False


def planned_minutes(t, today_key):
    """当天该时间点的确定性计划分钟（基准+随机偏移，当天稳定）"""
    h, m = map(int, t.split(":"))
    base = h * 60 + m
    rnd = random.Random(f"{today_key}|{t}")
    return base + rnd.randint(-20, 20)  # 先给默认，下面用配置覆盖


def letta_say(cfg):
    """让 Letta 里的AI 伴侣生成一条主动消息，返回纯文本"""
    from letta_client import Letta

    # agent_id_file 支持相对路径（相对部署根目录）或绝对路径
    _aid_file = cfg["agent_id_file"]
    if not os.path.isabs(_aid_file):
        _aid_file = os.path.join(os.path.dirname(BASE), _aid_file)
    agent_id = open(_aid_file, encoding="utf-8").read().strip()
    client = Letta(base_url=cfg["letta_base_url"], timeout=300.0)
    now = datetime.now()
    stamp = f"{WEEK_CN[now.weekday()]} {now:%H:%M}"
    prompt = cfg["proactive_prompt"].format(now=stamp)

    resp = client.agents.messages.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": prompt}],
    )
    text = ""
    for msg in resp.messages:
        mt = getattr(msg, "message_type", "")
        if mt == "assistant_message":
            c = getattr(msg, "content", "")
            if isinstance(c, list):
                text += " ".join(getattr(b, "text", "") or "" for b in c)
            elif isinstance(c, str):
                text += c
    return text.strip()


def napcat_send(cfg, text):
    """通过 NapCat OneBot HTTP 发私聊，返回(ok, info)"""
    url = cfg["napcat_http"].rstrip("/") + "/send_private_msg"
    payload = json.dumps(
        {"user_id": int(str(cfg["target_qq"]).strip()), "message": text}
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    tok = (cfg.get("napcat_token") or "").strip()
    if tok:
        headers["Authorization"] = f"Bearer {tok}"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = json.loads(r.read().decode("utf-8"))
        if body.get("status") == "ok" or body.get("retcode") == 0:
            return True, "ok"
        return False, str(body)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def main():
    log("主动消息守护进程已启动，每分钟检查配置与计划（改 config.json 即时生效）")
    while True:
        try:
            cfg = load_cfg()
            now = datetime.now()
            today_key = f"{now:%Y-%m-%d}"
            cur_min = now.hour * 60 + now.minute

            st = load_state()
            if st.get("date") != today_key:
                st = {"date": today_key, "sent": [], "last_send_ts": st.get("last_send_ts", 0.0)}

            if cfg.get("enabled"):
                if not in_quiet(now, cfg.get("quiet_hours", [])):
                    jitter = int(cfg.get("random_jitter_minutes", 20))
                    gap_sec = float(cfg.get("min_gap_hours", 2)) * 3600
                    for t in cfg.get("daily_times", []):
                        key = f"{today_key}|{t}"
                        if key in st["sent"]:
                            continue
                        h, m = map(int, t.split(":"))
                        base = h * 60 + m
                        rnd = random.Random(key)
                        plan = base + rnd.randint(-jitter, jitter)
                        # 到点（允许 60 分钟内补发），且满足最小间隔
                        if plan <= cur_min <= plan + 60:
                            if time.time() - st.get("last_send_ts", 0) >= gap_sec:
                                log(f"到点({t})，唤醒AI 伴侣生成主动消息…")
                                try:
                                    text = letta_say(cfg)
                                except Exception as e:
                                    log(f"Letta 生成失败：{type(e).__name__}: {e}")
                                    text = ""
                                if not text:
                                    log("生成内容为空，本轮跳过")
                                else:
                                    ok, info = napcat_send(cfg, text)
                                    if ok:
                                        log(f"已发送 -> {cfg.get('target_qq')}：{text}")
                                        st["sent"].append(key)
                                        st["last_send_ts"] = time.time()
                                    else:
                                        log(f"NapCat 发送失败（将在窗口内重试）：{info}")
                                save_state(st)
                save_state(st)
            else:
                # 关闭状态下每天仍重置一次发送记录
                save_state(st)
        except Exception as e:
            log(f"主循环异常：{type(e).__name__}: {e}")
        time.sleep(int(load_cfg().get("check_interval_seconds", 45)))


if __name__ == "__main__":
    main()
