# -*- coding: utf-8 -*-
"""
桌宠外观管理工具（AI 伴侣）
用法：
  python manage_model.py avatar <图片文件名>
      把 Open-LLM-VTuber/avatars 下的某张图设为当前头像，例如：
      python manage_model.py avatar ai_companion.png

  python manage_model.py install <模型目录> [模型英文名]
      把一个含 *.model3.json 的 Live2D 模型目录接入桌宠：
      自动复制到 live2d-models/<英文名>/、扫描动作与表情、登记 model_dict.json、并切换为当前模型。
      例：python manage_model.py install "C:\模型文件夹\my_live2d" my_model

  python manage_model.py use <模型英文名>
      仅把当前 Live2D 模型切换为 model_dict.json 里已登记的某个模型。
支持 Cubism 3/4/5 模型（.model3.json + .moc3），不支持 Cubism2。
"""
import json
import os
import shutil
import sys

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Open-LLM-VTuber")
CONF = os.path.join(ROOT, "conf.yaml")
DICT = os.path.join(ROOT, "model_dict.json")
MODELS_DIR = os.path.join(ROOT, "live2d-models")
AVATARS_DIR = os.path.join(ROOT, "avatars")

EMOTIONS = ["neutral", "anger", "disgust", "fear", "joy", "smirk", "sadness", "surprise"]


def load_dict():
    if os.path.isfile(DICT):
        return json.load(open(DICT, "r", encoding="utf-8"))
    return []


def save_dict(d):
    json.dump(d, open(DICT, "w", encoding="utf-8"), ensure_ascii=False, indent=4)


def find_model3(folder):
    for name in os.listdir(folder):
        if name.endswith(".model3.json"):
            return os.path.join(folder, name), name
    raise SystemExit("目录里没找到 *.model3.json，不是有效的 Live2D 模型目录：" + folder)


def scan_model(model3_path):
    """读取 model3.json，推断待机动作组与表情映射"""
    data = json.load(open(model3_path, "r", encoding="utf-8"))
    motions = data.get("Motions", data.get("motions", {})) or {}
    group_names = list(motions.keys())
    idle_group = "idle"
    for cand in ("idle", "Idle", "IDLE"):
        if cand in group_names:
            idle_group = cand
            break
    else:
        if group_names:
            idle_group = group_names[0]
    exprs = data.get("Expressions", data.get("expressions", [])) or []
    expr_names = [e.get("Name", e.get("name", "")) for e in exprs]
    n_expr = len(expr_names)
    emotion_map = {}
    for i, emo in enumerate(EMOTIONS):
        if n_expr == 0:
            emotion_map[emo] = 0
        else:
            # 没有语义标注时，均匀映射到不同表情，保证表情会变化
            emotion_map[emo] = min(i, n_expr - 1)
    tap = {}
    hit = data.get("HitAreas", data.get("hit_areas", [])) or []
    for h in hit:
        hid = h.get("Id", h.get("id", ""))
        if hid and group_names:
            tap[hid] = {group_names[0]: 1}
    return idle_group, emotion_map, tap, expr_names


def set_conf_field(key, value):
    s = open(CONF, "r", encoding="utf-8").read()
    lines = s.splitlines()
    hit = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(key + ":"):
            indent = line[: len(line) - len(stripped)]
            lines[i] = f"{indent}{key}: '{value}'"
            hit = True
    if not hit:
        raise SystemExit(f"conf.yaml 里没找到 {key} 字段")
    open(CONF, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def cmd_avatar(img):
    p = os.path.join(AVATARS_DIR, img)
    if not os.path.isfile(p):
        raise SystemExit(f"头像不存在：{p}（请先把图片放进 {AVATARS_DIR}）")
    set_conf_field("avatar", img)
    print("头像已切换为", img)


def cmd_install(src, name=None):
    src = os.path.abspath(src)
    _, model3_name = find_model3(src)
    if not name:
        name = os.path.basename(src.rstrip("\\/"))
    name = name.replace(" ", "_")
    dst = os.path.join(MODELS_DIR, name)
    if os.path.abspath(src) != os.path.abspath(dst):
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print("模型已复制到", dst)
    m3, _ = find_model3(dst)
    idle, emap, tap, expr_names = scan_model(m3)
    url = f"/live2d-models/{name}/{os.path.basename(m3)}"
    entry = {
        "name": name,
        "description": name,
        "url": url,
        "kScale": 0.4,
        "initialXshift": 0,
        "initialYshift": 0,
        "idleMotionGroupName": idle,
        "defaultEmotion": 0,
        "emotionMap": emap,
    }
    if tap:
        entry["tapMotions"] = tap
    d = load_dict()
    d = [e for e in d if e.get("name") != name]
    d.append(entry)
    save_dict(d)
    set_conf_field("live2d_model_name", name)
    print("已登记并切换为模型：", name)
    print("待机动作组：", idle, "| 表情数：", len(expr_names), expr_names)
    print("前端刷新即可看到；若大小/位置不合适，在界面滚轮缩放，或改 model_dict.json 的 kScale/initialXshift/initialYshift。")


def cmd_use(name):
    d = load_dict()
    if not any(e.get("name") == name for e in d):
        raise SystemExit(f"model_dict.json 里没有模型 {name}，现有：{[e.get('name') for e in d]}")
    set_conf_field("live2d_model_name", name)
    print("当前 Live2D 模型已切换为", name)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(0)
    cmd = sys.argv[1]
    if cmd == "avatar":
        cmd_avatar(sys.argv[2])
    elif cmd == "install":
        cmd_install(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == "use":
        cmd_use(sys.argv[2])
    else:
        print(__doc__)
