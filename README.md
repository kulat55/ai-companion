# AICompanion · AI 伴侣

一个基于 [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) + [Letta](https://github.com/letta-ai/letta) + Ollama 深度定制的 **本地 AI 伴侣** 项目。

她是一个住在你电脑里的 AI 角色——有完整人设记忆（人格可自定义）、能感知时间和天气、会主动找你聊天（QQ）、有可视化桌宠和网页管理面板。

> ⚠️ 本仓库为**定制层开源**：运行时会自动 clone 上游 Open-LLM-VTuber，本仓库只包含定制脚本、配置模板与使用手册。

---

## ✨ 功能特性

| 能力 | 说明 |
|---|---|
| 🧠 **长期记忆** | 基于 Letta 的三层记忆（核心记忆 / 对话历史 / 归档检索），她记得你的一切 |
| 👤 **拟人化人格** | 完整人设模板（可自定义角色背景、性格、说话方式），说话像真人发微信 |
| 🕐 **时间感知** | System Prompt 自动注入当前时间，她知道现在是几点、该干嘛 |
| 🌦️ **天气感知** | 每日定时抓取本地天气写入记忆，她知道今天冷不冷、要不要带伞 |
| 💬 **对话模型可选** | DeepSeek Flash（便宜快）/ DeepSeek R1（深度思考）/ 本地 Ollama qwen2.5（离线备用） |
| 🖥️ **网页管理面板** | 状态总览、服务健康灯、一键诊断、模型切换、记忆编辑、对话历史检索 |
| 🐱 **桌宠模式** | 桌面悬浮 Live2D 角色，时间心情气泡、打开问候 |
| 💌 **主动联系（QQ）** | 定时主动给你发 QQ 消息（NapCat 协议框架），像真人一样维系感情 |
| 🎙️ **语音** | edge-tts 语音合成，她会"开口说话" |

---

## 📁 项目结构

```
<部署根>/                          # 本仓库 clone 到任意目录即可（如 D:\AICompanion）
├── companion/                   # 控制脚本（记忆 / 模型切换 / 主动消息 / QQ 控制）
│   ├── memory.py                # 记忆查看 / 编辑 / 导出
│   ├── model_switch.py          # 模型切换（deepseek / local）
│   ├── manage_model.py          # Live2D 模型管理
│   ├── proactive_sender.py      # 定时主动发 QQ 守护进程
│   ├── config.example.json      # 配置模板（复制为 config.json 后填写）
│   ├── Modelfile.qwen7b        # 本地 Ollama 模型定义（7b，加大上下文防空回复）
│   ├── Modelfile.qwen3b        # 本地 Ollama 模型定义（3b，更省显存）
│   └── *.ps1                    # QQ 开关 / 守护启停脚本
├── desktop/backend.py           # 一键启动编排后端（PG→Letta→桌宠全自动）
│   ├── inject_frontend.py       # 自动注入网页管理面板（幂等，零改动）
│   └── frontend_patch.html      # 管理面板/心情/问候/诊断/试听 中性模板
├── letta-server/                # 记忆服务脚本
│   ├── init_pg.py               # 内嵌 PostgreSQL 初始化
│   ├── create_agent.py          # 创建 AI 伴侣智能体（可自定义人设）
│   └── setup_openai_ds.py       # 注册 DeepSeek provider
├── conf.yaml.example            # Open-LLM-VTuber 配置模板（安装时自动填入 agent id）
├── setup.ps1                    # ★ 一键安装（clone 上游/装依赖/起服务/建智能体）
├── start_all.ps1 / stop_all.ps1 # 一键启停全部服务
├── status_all.ps1               # 查看服务状态
├── test_all.py                  # 全面功能测试脚本
└── 使用说明.md                  # 详细部署与运维手册
```

> 运行时数据（**不属于本仓库，请勿提交/共享**）：`letta-data/`（记忆数据库）、`pgdata/`（PostgreSQL 数据）、`Open-LLM-VTuber/chat_history/`（对话历史）、`companion/deepseek_key.txt`（API 密钥）、`napcat/`（QQ 协议框架）。

---

## 🚀 快速开始（下载即用）

### 前置依赖

- Windows 10/11
- [Git](https://git-scm.com/download/win)
- Python 3.10+（安装时勾选 **Add to PATH**）
- [Ollama](https://ollama.com/download)（本地嵌入/离线模型需要，强烈建议）
- DeepSeek API Key（云端对话大脑，https://platform.deepseek.com 创建）

### 第 1 步：clone 本仓库

```powershell
git clone https://github.com/kulat55/ai-companion.git D:\AICompanion
cd D:\AICompanion
```

### 第 2 步：一键安装

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

脚本会自动完成（全程约 5-15 分钟，视网速）：
0. 检查 git / python 前置工具
1. 创建 Letta 虚拟环境并安装依赖（letta 0.16.8 / pgserver / edge-tts）
2. clone 上游 Open-LLM-VTuber 并安装其依赖
3. 生成 `companion\config.json`（模板）
4. 提示输入 DeepSeek API Key（也可手动创建 `companion\deepseek_key.txt`）
5. 初始化内嵌 PostgreSQL → 启动 Letta 记忆大脑
6. 注册 DeepSeek 模型通道
7. 创建"AI 伴侣"智能体（人设在 `letta-server\create_agent.py` 里自定义）
8. 生成 `Open-LLM-VTuber\conf.yaml`（自动填入 agent id）

### 第 3 步：配置（编辑 companion\config.json）

| 字段 | 说明 |
|---|---|
| `bot_self_qq` | 发消息的 QQ 小号（仅主动消息功能需要） |
| `target_qq` | 接收消息的主 QQ 号 |
| `city` | 天气感知的城市，如 "苏州" |
| `daily_times` | 主动发消息的时间点 |

### 第 4 步：启动

```powershell
.\start_all.ps1     # 启动全部服务（PG → Letta → 桌宠）
.\status_all.ps1    # 查看服务状态
.\stop_all.ps1      # 停止全部服务
```

然后浏览器打开 **http://localhost:12393** 开始聊天。

> 提示：所有脚本都用相对路径定位（`$PSScriptRoot` / `Path(__file__)`），**clone 到任意目录都能运行**，不依赖固定盘符。

---

## 💬 使用

### 网页聊天

打开 <http://localhost:12393>，右下角 ⚙ 悬浮按钮打开管理面板（自动注入，无需额外配置）。

### 管理面板功能

- **状态**：服务健康检查（Letta 记忆大脑 / Ollama）、一键诊断、TTS 试听
- **模型**：下拉切换对话模型（DeepSeek / 本地 Ollama qwen），实时生效
- **记忆**：直接编辑"人格"和"关于你"两个核心记忆块，一键保存
- **历史**：查看最近 20 条对话记录

> 完整管理能力（记忆导出/检索、模型状态详情、主动消息）见下方命令行脚本。

### 记忆操作（命令行）

```powershell
$py = "$PWD\letta-server\venv\Scripts\python.exe"
& $py companion\memory.py show              # 看她的核心记忆
& $py companion\memory.py edit human        # 编辑"关于你"
& $py companion\memory.py edit persona      # 编辑她的人格
& $py companion\memory.py append human "新信息"
& $py companion\memory.py history 30        # 最近 30 条对话
& $py companion\memory.py export            # 导出全部记忆
```

### 模型切换（命令行）

```powershell
& $py companion\model_switch.py status      # 当前模型
& $py companion\model_switch.py deepseek    # 切 DeepSeek（读 deepseek_key.txt）
& $py companion\model_switch.py local       # 切本地 qwen（需先开 Ollama）
```

### 主动发 QQ

```powershell
powershell -File companion\start_proactive.ps1   # 启动守护
powershell -File companion\qq_on.ps1             # 开启定时主动发
& $py companion\send_now.py --send              # 立刻真发一条测试
powershell -File companion\qq_off.ps1           # 关闭
powershell -File companion\stop_proactive.ps1   # 停掉守护
```

### 天气自动更新

```powershell
# 1. 在 companion\config.json 里设置 city（如 "苏州"）
# 2. 设置 Windows 任务计划，每天 07:30 运行：
#    程序:   <部署根>\letta-server\venv\Scripts\python.exe
#    参数:   <部署根>\update_weather.py
#    起始于: <部署根>
```

### 自定义她的人格

编辑 `letta-server\create_agent.py` 里的 `PERSONA`（人设）和 `HUMAN`（关于用户）段落，然后重新运行：

```powershell
& $py letta-server\create_agent.py
```

---

## 🧪 测试

```powershell
& $py test_all.py     # $py = "<部署根>\letta-server\venv\Scripts\python.exe"
```

覆盖：服务端口、Letta API、记忆读写、对话往返（发消息验证不空回复）、TTS、前端页面完整性。全绿 = 一切正常。

---

## 🔧 常见问题（FAQ）

**Q: 她回复空内容 / 一句话都不说？**
A: 本地模型上下文窗口太小会"空回复"。使用本仓库的 Modelfile 创建模型：
```powershell
ollama create qwen2.5:7b-companion  -f companion\Modelfile.qwen7b     # 7b，num_ctx 6144，适配 4GB 显存
ollama create qwen2.5:3b-companion  -f companion\Modelfile.qwen3b     # 3b，更省显存，num_ctx 8192
```
创建后用 `python companion\model_switch.py local` 切到本地模型（默认 qwen2.5:7b-companion；若只用 3b，请把 `model_switch.py` 里的 `LOCAL_MODEL` 改为 `ollama-local/qwen2.5:3b-companion`）。

**Q: 网页管理面板报 "Failed to fetch"？**
A: 这是 Letta 的 CORS 问题。setup.ps1 启动 Letta 时已带 `ACCEPTABLE_ORIGINS`；若手动启动 Letta，必须加上：
```powershell
$env:ACCEPTABLE_ORIGINS = "http://localhost:12393,http://127.0.0.1:12393,http://localhost:8283,http://127.0.0.1:8283"
```

**Q: 桌宠模式看不到聊天文字？**
A: 桌宠模式（`?pet=1`）刻意隐藏了左栏，用完整网页 `http://localhost:12393` 查看。

**Q: 听不到她说话？**
A: 浏览器自动播放策略：先在页面上点击一下（如点输入框），之后再说话就有声音。

**Q: 记忆数据库健康灯一直"检测中/红灯"？**
A: PG 不是 HTTP 服务，健康灯以 Letta 在线为准（Letta 在线即 PG 在线）。

---

## 📜 开源说明

- 本仓库按 **MIT License** 开源，见 [LICENSE](LICENSE)
- 上游依赖：Open-LLM-VTuber（MIT）、Letta（Apache-2.0）、Ollama、NapCat、edge-tts，各按其许可证使用
- 请勿提交：API 密钥、QQ 号、记忆数据库、对话历史、模型权重等隐私与运行时数据

## 🤝 贡献

欢迎提 Issue / PR。好的贡献方向：人格模板、更多 TTS 接入、主动消息策略优化、多语言支持。

---

**Made with ❤️ for kulat55 and his AI 伴侣**
