# ============================================================
# AI 伴侣 · 一键安装脚本（Windows）
# 在"部署根目录"（本仓库 clone 到的位置）运行：
#   powershell -ExecutionPolicy Bypass -File setup.ps1
#
# 自动完成：
#   1) 检查 git / python
#   2) 创建 letta-server 虚拟环境并安装 Letta(0.16.8)+pgserver+edge-tts
#   3) clone 上游 Open-LLM-VTuber 并安装其依赖
#   4) 生成 companion\config.json（从模板）
#   5) 提示填写 DeepSeek API Key
#   6) 初始化内嵌 PostgreSQL -> 启动 Letta 记忆大脑
#   7) 打 DeepSeek 模型名补丁、注册 deepseek provider
#   8) 创建"AI 伴侣"智能体并写入 AGENT_ID.txt
#   9) 生成 Open-LLM-VTuber\conf.yaml（自动填 agent id）
#   完成后运行 start_all.ps1 即可开始聊天。
# ============================================================
$ROOT = $PSScriptRoot
$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'AI 伴侣 一键安装'

function Step($msg) { Write-Host "`n>>> $msg" -ForegroundColor Cyan }
function Ok($msg)    { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "  [!] $msg" -ForegroundColor Yellow }

Write-Host "==============================================" -ForegroundColor Magenta
Write-Host "  AI 伴侣 一键安装" -ForegroundColor Magenta
Write-Host "  部署根目录: $ROOT" -ForegroundColor Magenta
Write-Host "==============================================" -ForegroundColor Magenta

# ---------- 1. 前置检查 ----------
Step "1/9 检查前置工具（git / python）"
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) { throw "未找到 git，请先安装 https://git-scm.com/download/win 后重试" }
Ok "git: $($gitCmd.Source)"
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) { throw "未找到 python，请先安装 Python 3.10+（勾选 Add to PATH）后重试" }
$pyVer = & python --version 2>&1
Ok "python: $pyVer"

# ---------- 2. Letta 虚拟环境 ----------
$lettaVenv = Join-Path $ROOT 'letta-server\venv'
if (Test-Path (Join-Path $lettaVenv 'Scripts\python.exe')) {
    Ok "letta-server venv 已存在，跳过创建"
} else {
    Step "2/9 创建 Letta 虚拟环境并安装依赖（letta 0.16.8 / letta-client / pgserver / edge-tts，约几分钟）"
    New-Item -ItemType Directory -Path (Join-Path $ROOT 'letta-server') -Force | Out-Null
    python -m venv $lettaVenv
    if (-not (Test-Path (Join-Path $lettaVenv 'Scripts\python.exe'))) { throw "venv 创建失败" }
    & (Join-Path $lettaVenv 'Scripts\python.exe') -m pip install --upgrade pip --quiet
    & (Join-Path $lettaVenv 'Scripts\pip.exe') install "letta[server]==0.16.8" "letta-client==1.12.1" "pgserver" "requests" "edge-tts" 2>&1 | Select-Object -Last 3
    if ($LASTEXITCODE -ne 0) { throw "letta 依赖安装失败，请检查网络后重试" }
}
$lettaPy = Join-Path $lettaVenv 'Scripts\python.exe'
Ok "letta venv 就绪"

# ---------- 3. 上游 Open-LLM-VTuber ----------
$vtRoot = Join-Path $ROOT 'Open-LLM-VTuber'
if (Test-Path (Join-Path $vtRoot 'run_server.py')) {
    Ok "Open-LLM-VTuber 已存在，跳过 clone"
} else {
    Step "3/9 clone 上游 Open-LLM-VTuber"
    git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git $vtRoot
    if (-not (Test-Path (Join-Path $vtRoot 'run_server.py'))) { throw "clone 失败" }
}
$vtVenv = Join-Path $vtRoot '.venv'
if (Test-Path (Join-Path $vtVenv 'Scripts\python.exe')) {
    Ok "上游 .venv 已存在，跳过安装"
} else {
    Step "3b. 安装上游依赖（Open-LLM-VTuber requirements.txt，约几分钟）"
    python -m venv $vtVenv
    & (Join-Path $vtVenv 'Scripts\python.exe') -m pip install --upgrade pip --quiet
    & (Join-Path $vtVenv 'Scripts\pip.exe') install -r (Join-Path $vtRoot 'requirements.txt') 2>&1 | Select-Object -Last 3
    if ($LASTEXITCODE -ne 0) { throw "上游依赖安装失败" }
}
Ok "上游就绪"

# ---------- 4. 生成 config.json ----------
$cfg = Join-Path $ROOT 'companion\config.json'
if (Test-Path $cfg) {
    Ok "companion\config.json 已存在，跳过（可手动修改 QQ 号/城市/时间）"
} else {
    Step "4/9 生成 companion\config.json（模板）"
    Copy-Item (Join-Path $ROOT 'companion\config.example.json') $cfg
    Warn "请稍后编辑 companion\config.json：bot_self_qq（发消息的小号）、target_qq（接收的主号）、city（城市）"
}

# ---------- 5. DeepSeek API Key ----------
$keyFile = Join-Path $ROOT 'companion\deepseek_key.txt'
if (Test-Path $keyFile) {
    Ok "deepseek_key.txt 已存在"
} else {
    Step "5/9 配置 DeepSeek API Key"
    Write-Host "  请到 https://platform.deepseek.com 创建 API Key，然后："
    Write-Host "  (a) 把 key 粘贴到下面（回车确认）"
    Write-Host "  (b) 或手动创建 companion\deepseek_key.txt 后重新运行本脚本"
    $k = Read-Host "  请输入 DeepSeek API Key（sk-开头，直接回车=跳过稍后手动填）"
    if ($k -and $k.StartsWith('sk-')) {
        [IO.File]::WriteAllText($keyFile, $k.Trim(), (New-Object Text.UTF8Encoding $false))
        Ok "已写入 deepseek_key.txt"
    } else {
        Warn "跳过。请在运行前手动创建 companion\deepseek_key.txt（内容为 sk- 开头的 key）"
    }
}

# ---------- 6. 初始化 PG + 启动 Letta ----------
Step "6/9 初始化内嵌 PostgreSQL 并启动 Letta 记忆大脑"
$lettaExe = Join-Path $lettaVenv 'Scripts\letta.exe'
# 6a. PG
& $lettaPy (Join-Path $ROOT 'letta-server\init_pg.py') 2>&1 | Select-Object -Last 5
if ($LASTEXITCODE -ne 0) { throw "内嵌 PostgreSQL 初始化失败" }
$pgport = (Get-Content (Join-Path $ROOT 'pgdata\PORT') -ErrorAction SilentlyContinue).Trim()
if (-not $pgport) { $pgport = '55432' }
Ok "PostgreSQL 就绪 (端口 $pgport)"

# 6b. Letta server（后台）
$lettaData = Join-Path $ROOT 'letta-data'
New-Item -ItemType Directory -Path $lettaData -Force | Out-Null
$env:LETTA_DIR = $lettaData
$env:LETTA_DISABLE_TRACING = 'true'
$env:ACCEPTABLE_ORIGINS = 'http://localhost:12393,http://127.0.0.1:12393,http://localhost:8283,http://127.0.0.1:8283'
$env:LETTA_PG_URI = "postgresql+pg8000://letta:letta@127.0.0.1:$pgport/letta"
if (Test-Path $keyFile) { $env:DEEPSEEK_API_KEY = (Get-Content $keyFile).Trim() }

$already = Get-Process -Name 'letta' -ErrorAction SilentlyContinue
if (-not $already) {
    Start-Process -FilePath $lettaExe -ArgumentList 'server','--type','rest','--host','localhost','--port','8283' -WindowStyle Hidden
}
Ok "等待 Letta 就绪（约 10-60 秒）…"
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8283/v1/health/' -TimeoutSec 3 -UseBasicParsing
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
}
if (-not $ready) { throw "Letta 未在 80 秒内就绪，请查看 letta-server\letta.log / letta.err.log" }
Ok "Letta 记忆大脑已就绪 (http://127.0.0.1:8283)"

# ---------- 7. DeepSeek 补丁 + provider ----------
Step "7/9 打 DeepSeek 模型名补丁并注册 provider"
& $lettaPy (Join-Path $ROOT 'companion\_patch_deepseek.py') 2>&1 | Select-Object -Last 2
& $lettaPy (Join-Path $ROOT 'letta-server\setup_openai_ds.py') 2>&1 | Select-Object -Last 4
Ok "DeepSeek 接入完成"

# ---------- 8. 创建智能体 ----------
Step "8/9 创建 AI 伴侣智能体（写入 AGENT_ID.txt）"
# 可选：Ollama bge-m3 嵌入模型
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    $models = & ollama list 2>&1
    if ($models -notmatch 'bge-m3') {
        Warn "检测到 Ollama 但未安装 bge-m3 嵌入模型，正在拉取（约 1GB，可跳过）…"
        & ollama pull bge-m3 2>&1 | Select-Object -Last 2
    }
} else {
    Warn "未检测到 Ollama：create_agent 需要本地 bge-m3 嵌入模型，请先安装 Ollama 并 ollama pull bge-m3，或改 letta-server\create_agent.py 中的 EMBED_MODEL"
}
& $lettaPy (Join-Path $ROOT 'letta-server\create_agent.py') 2>&1 | Select-Object -Last 10
if ($LASTEXITCODE -ne 0) { throw "创建智能体失败，请按上面提示处理 Ollama/嵌入模型后重试" }
$aid = (Get-Content (Join-Path $ROOT 'letta-server\AGENT_ID.txt') -ErrorAction SilentlyContinue).Trim()
if (-not $aid) { throw "AGENT_ID.txt 未生成" }
Ok "智能体已创建 (id: $aid)"

# ---------- 9. 生成 conf.yaml ----------
Step "9/9 生成 Open-LLM-VTuber\conf.yaml"
$confTpl = Join-Path $ROOT 'conf.yaml.example'
$confDst = Join-Path $vtRoot 'conf.yaml'
$confText = Get-Content $confTpl -Raw -Encoding UTF8
$confText = $confText.Replace('YOUR_AGENT_ID', $aid)
[IO.File]::WriteAllText($confDst, $confText, (New-Object Text.UTF8Encoding $false))
Ok "conf.yaml 已写入 agent id"

Write-Host "`n==============================================" -ForegroundColor Magenta
Write-Host "  安装完成！" -ForegroundColor Magenta
Write-Host "  1) 编辑 companion\config.json（QQ 号 / 城市 / 发送时间）" -ForegroundColor White
Write-Host "  2) 运行 start_all.ps1 启动全部服务" -ForegroundColor White
Write-Host "  3) 浏览器打开 http://localhost:12393 开始聊天" -ForegroundColor White
Write-Host "==============================================" -ForegroundColor Magenta
