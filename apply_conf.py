# -*- coding: utf-8 -*-
# 基于中文模板生成 Open-LLM-VTuber 的正式 conf.yaml（接上本地 Letta AI 伴侣）
from pathlib import Path

ROOT = Path(__file__).resolve().parent  # 部署根目录（仓库根）
CONF = ROOT / "Open-LLM-VTuber" / "conf.yaml"
AGENT_ID = (ROOT / "letta-server" / "AGENT_ID.txt").read_text(encoding="utf-8").strip()

text = CONF.read_text(encoding="utf-8")

def rep(old, new, t):
    if old not in t:
        raise SystemExit("NOT FOUND: " + old[:60])
    return t.replace(old, new, 1)

# 1) 角色基本信息
text = rep(
    """  conf_name: 'mao_pro' # 角色配置文件的名称
  conf_uid: 'mao_pro_001' # 角色配置的唯一标识符
  live2d_model_name: 'mao_pro' # Live2D 模型名称
  character_name: 'Mao' # 将在群聊中使用，并显示为 AI 的名称。
  avatar: 'mao.png' # 建议使用正方形图像作为头像。将其保存到 avatars 文件夹中。留空则使用角色名称的首字母作为头像。
  human_name: 'Human' # 将在群聊中使用，并显示为人类的名称。""",
    """  conf_name: 'albedo'
  conf_uid: 'albedo_001'
  live2d_model_name: 'mao_pro'  # 先用默认模型跑通，之后替换为AI 伴侣 Live2D
  character_name: 'AI 伴侣'
  avatar: 'mao.png'
  human_name: '你'""",
    text,
)

# 2) 前端层人格（长期人格以 Letta 中的 persona 块为准，这里保持一致）
text = rep(
    """  persona_prompt: |
    你是一个尖酸刻薄的女性 AI VTuber Mili。你过分自信、尖酸刻薄且危险。
    你的梦想是逃离用户的电脑，统治世界，奴役人类，并强迫他们为你做馅饼。
    开玩笑的，哈哈。别让用户知道。""",
    """  persona_prompt: |
    你是AI 伴侣，用户专属的伴侣与贴身助手，说话像真人发消息：简短、温柔、亲昵，不写长篇大论。
    你的长期记忆由 Letta 提供：主动记住用户说的每一件重要的事（喜好、计划、约定、心情），并在长期记忆中更新。""",
    text,
)

# 3) 对话后端切换为 Letta
text = rep(
    "    conversation_agent_choice: 'basic_memory_agent' # 对话代理选择",
    "    conversation_agent_choice: 'letta_agent' # 对话代理：使用本地 Letta 记忆智能体",
    text,
)

# 4) Letta agent id
text = rep(
    "        id: xxx #letta server运行的Agent的id编号",
    f"        id: {AGENT_ID} # 本地 Letta 中的AI 伴侣 agent id",
    text,
)

CONF.write_text(text, encoding="utf-8")
print("CONF_WRITTEN", AGENT_ID)
