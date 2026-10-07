# AICompanion · AI 伴侣 AI 伴侣

一个基于 [Open-LLM-VTuber](https://github.com/Open-LLM-VTuber/Open-LLM-VTuber) + [Letta](https://github.com/letta-ai/letta) + Ollama 深度定制的 **本地 AI 伴侣** 项目。

她是一个住在你电脑里的"女大学生"——有完整人设记忆、能感知时间和天气、会主动找你聊天（QQ）、有可视化桌宠和网页管理面板。

> ⚠️ 本仓库为**定制层开源**：上游 Open-LLM-VTuber 本体请从官方仓库获取（见下方安装说明），本仓库只包含定制脚本、配置模板与使用手册。

---

## ✨ 功能特性

| 能力 | 说明 |
|---|---|
| 🧠 **长期记忆** | 基于 Letta 的三层记忆（核心记忆 / 对话历史 / 归档检索），她记得你的一切 |
| 👤 **拟人化人格** | 完整人设（女大学生"苏雅"），从出生到大学的记忆背景，说话像真人发微信 |
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
AICompanion/                     # 你的本地部署根目录（本仓库为定制层）
├── companion/                   # 控制脚本（记忆 / 模型切换 / 主动消息 / QQ 控制）
│   ├── memory.py                # 记忆查看 / 编辑 / 导出
│   ├── model_switch.py          # 模型切换（deepseek / local）
│   ├── manage_model.py          # Live2D 模型管理
│   ├── proactive_sender.py      # 定时主动发 QQ 守护进程
│   ├── config.example.json      # 主动消息配置模板（复制为 config.json 后填写）
│   ├── Modelfile.qwen-albedo    # 本地 Ollama 模型定义（8k 上下文防空回复）
│   └── *.ps1                    # QQ 开关 / 守护启停脚本
├── update_weather.py            # 每日更新天气到记忆
├── apply_conf.py                # 将当前 agent 配置写入 conf.yaml
├── start_all.ps1 / stop_all.ps1 # 一键启停全部服务
├── status_all.ps1               # 查看服务状态
├── test_all.py                  # 全面功能测试脚本
└── 使用说明.md                  # 详细部署与运维手册
```

> 运行时数据（**不属于本仓库，请勿提交/共享**）：`letta-data/`（记忆数据库）、`pgdata/`（PostgreSQL 数据）、`Open-LLM-VTuber/chat_history/`（对话历史）、`companion/deepseek_key.txt`（API 密钥）、`napcat/`（QQ 协议框架）。

---

## 🚀 快速开始

### 前置依赖

- Windows 10/11
- [Git](https://git-scm.com/download/win)
- Python 3.10+（建议用 uv 或 venv）
- [Ollama](https://ollama.com/download)（可选，本地模型需要）
- DeepSeek API Key（推荐，云端模型需要）

### 1. 获取上游项目

```powershell
git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git
```

### 2. 安装后端服务

**Letta（记忆大脑，端口 8283）**

```powershell
# 需要 PostgreSQL（端口 55432）
pip install letta
# 或参考 Letta 官方文档：https://docs.letta.com
```

启动 Letta 时**必须**带上 CORS 白名单，否则网页管理面板无法访问：

```powershell
$env:LETTA_DIR = "$PWD\letta-data"
$env:LETTA_PG_URI = "postgresql+pg8000://letta:letta@127.0.0.1:55432/letta"
$env:ACCEPTABLE_ORIGINS = "http://localhost:12393,http://127.0.0.1:12393"
letta server --type rest --host localhost --port 8283
```

**Open-LLM-VTuber（前端 + 桌宠，端口 12393）**

```powershell
cd Open-LLM-VTuber
pip install -r requirements.txt
python run_server.py
```

### 3. 配置 DeepSeek 密钥

创建 `companion/deepseek_key.txt`，粘贴你的 API Key：

```powershell
New-Item -ItemType File companion\deepseek_key.txt
notepad companion\deepseek_key.txt   # 粘贴 sk-xxxx 后保存
```

### 4. 配置主动消息（可选，QQ）

```powershell
Copy-Item companion\config.example.json companion\config.json
notepad companion\config.json   # 填你的 QQ 号（bot_self_qq / target_qq）
```

### 5. 一键启停

```powershell
.\start_all.ps1     # 启动全部服务（PG → Letta → VTuber → Ollama）
.\status_all.ps1    # 查看服务状态
.\stop_all.ps1      # 停止全部服务
```

---

## 💬 使用

### 网页聊天

打开 <http://localhost:12393>，左下角 FAB 按钮打开管理面板。

### 管理面板功能

- **状态**：服务健康灯（记忆数据库/记忆大脑/桌宠）、Ollama 显存、她上次说话时间、一键诊断、试听声音
- **切换模型**：DeepSeek Flash（省钱）/ DeepSeek R1（深度思考）/ 本地 qwen（离线）
- **核心记忆**：直接编辑"人格"和"关于你"两个记忆块，Ctrl+S 保存
- **对话历史**：搜索 / 分页查看所有聊天记录

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
# 修改 update_weather.py 里的城市名（默认苏州），然后设置 Windows 任务计划每天运行：
#   程序: python.exe
#   参数: D:\AICompanion\update_weather.py
#   时间: 每天 07:30
```

---

## 🧪 测试

```powershell
python test_all.py
```

覆盖：服务端口、Letta API、记忆读写、对话往返（发消息验证不空回复）、TTS、前端页面完整性。全绿 = 一切正常。

---

## 🔧 常见问题（FAQ）

**Q: 她回复空内容 / 一句话都不说？**
A: 本地模型上下文窗口太小会"空回复"。使用本仓库的 Modelfile 创建模型：
```powershell
ollama create qwen2.5:7b-albedo -f companion\Modelfile.qwen-albedo
```
（已设 `num_ctx 6144`，适配 4GB 显存机器）

**Q: 网页管理面板报 "Failed to fetch"？**
A: Letta 启动时漏了 `ACCEPTABLE_ORIGINS`，按上文重启即可。

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

**Made with ❤️ for 宇涵 and his AI 伴侣**
