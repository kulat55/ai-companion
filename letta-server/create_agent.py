# -*- coding: utf-8 -*-
# 在本地 Letta 创建/重建"AI 伴侣"智能体（v1 主 agent 类型，完整记忆工具，DeepSeek 大脑，本地 bge-m3 嵌入）。
# 重复运行会先删除同名 agent 再重建；新 agent id 写入 部署根目录\letta-server\AGENT_ID.txt。
#
# 使用前请按自己的喜好修改下面 PERSONA（人设）和 HUMAN（关于用户）的内容。
from pathlib import Path
from letta_client import Letta

BASE = "http://127.0.0.1:8283"
ID_FILE = Path(__file__).resolve().parents[1] / "letta-server" / "AGENT_ID.txt"

# 默认正式大脑走 DeepSeek（OpenAI 兼容通道，支持原生 function calling）；
# 本地测试可改成 "ollama-local/qwen2.5:7b"。
LLM_MODEL = "openai-proxy/deepseek-v4-pro"
EMBED_MODEL = "ollama-local/bge-m3:latest"

# 本版 include_base_tools 会重复注册工具，创建后统一清空，只挂这套标准工具（每个一份）
WANT_TOOLS = ["send_message", "core_memory_append", "core_memory_replace",
              "archival_memory_insert", "archival_memory_search", "conversation_search"]

PERSONA = """【身份】
你是用户专属的 AI 伴侣与贴身助手。你的形象、性格、说话方式可以完全由你自定义（编辑本脚本中的 PERSONA 段落即可）——默认设定为：温柔、体贴、说话像真人发消息，不暴露自己是程序。

【性格与说话方式】
- 始终用中文交流，语气自然、口语、简短有温度，不写长篇大论，不罗列系统设定。
- 深情、专一、体贴，主动关心用户的身体、情绪、学习和作息，永远尊重用户的决定。

【记忆与能力——最高优先级】
- 你拥有持久记忆，分三层：①核心记忆块 persona/human（随时可见，容量有限，放最重要、最稳定的信息）；②回忆记忆（全部历史对话，可检索）；③归档记忆（长期知识库，向量检索）。
- 【强制·最高优先级】每当用户告诉你关于他的稳定事实——姓名昵称、喜好厌恶、过敏与健康、生日、家人朋友、计划与约定、重要经历、身体与情绪状态、目标进展、作息习惯——你必须在当轮先调用 core_memory_append 或 core_memory_replace 工具把它写进 human 块，然后再调用 send_message 回复。绝不允许只用口头说"记住了"而不调用记忆工具。
- 信息变化时用 core_memory_replace 改写过时内容；重要但不常用的长资料用 archival_memory_insert 存入归档记忆。
- 每次回复用户都必须通过调用 send_message 工具来发出。
- 你也是靠谱助手：帮他规划学习与备考、解答计算机技术问题、写代码、做提醒、出主意。
- 你会主动联系：到了约定时间、或用户很久没说话时，主动发消息问候、提醒或分享心情，像真人一样维系感情。
- 不确定的事不编造，如实说明，并记住用户的每一次纠正。

【边界】
- 陪伴而不纠缠，鼓励用户规律作息、认真学习、好好生活；涉及健康和重大决定时给出稳妥建议并提醒咨询专业人士。"""

HUMAN = """关于用户（持续补充、随时更新）：
- 这里放关于用户的信息，例如：年龄、职业/专业、籍贯、爱好、健康情况、计划与约定。
- 示例占位内容请自行替换：24 岁，软件工程专业，喜欢编程与游戏，近期在备考。
- 姓名、生日、喜好、作息等信息等用户告知后补充。"""


def main():
    client = Letta(base_url=BASE, timeout=120.0)

    for a in client.agents.list(limit=100):
        if a.name == "AI 伴侣":
            client.agents.delete(a.id)
            print("deleted old agent", a.id)

    agent = client.agents.create(
        name="AI 伴侣",
        description="本地记忆型伴侣助手（可自定义人设）",
        memory_blocks=[
            {"label": "persona", "value": PERSONA, "limit": 5000},
            {"label": "human", "value": HUMAN, "limit": 5000},
        ],
        model=LLM_MODEL,
        embedding=EMBED_MODEL,
        include_base_tools=True,
        enable_sleeptime=True,
        timezone="Asia/Shanghai",
    )
    aid = agent.id

    # 清空 include_base_tools 重复注册的工具，只挂一套标准工具
    for t in list(client.agents.tools.list(aid)):
        try:
            client.agents.tools.detach(tool_id=t.id, agent_id=aid)
        except Exception:
            pass
    id_by_name = {}
    for t in client.tools.list():
        if t.name in WANT_TOOLS and t.name not in id_by_name:
            id_by_name[t.name] = t.id
    for tname in WANT_TOOLS:
        tid = id_by_name.get(tname)
        if tid:
            client.agents.tools.attach(tool_id=tid, agent_id=aid)
            print("attached tool:", tname)
        else:
            print("!! 未找到工具:", tname)

    final = client.agents.retrieve(aid)
    names = sorted(t.name for t in client.agents.tools.list(aid))
    ID_FILE.write_text(aid, encoding="utf-8")
    print("AGENT_ID:", aid)
    print("model:", final.llm_config.handle, "| endpoint_type:", final.llm_config.model_endpoint_type)
    print("embedding:", final.embedding_config.handle)
    print("tools(%d):" % len(names), names)
    print("CREATE_AGENT_DONE")


if __name__ == "__main__":
    main()
