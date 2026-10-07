# 开启“AI 伴侣主动发QQ”总开关（守护进程需已在运行；若没运行请先 start_proactive.ps1）
$ROOT = Split-Path $PSScriptRoot -Parent
$py = Join-Path $ROOT 'letta-server\venv\Scripts\python.exe'
& $py (Join-Path $PSScriptRoot 'set_flag.py') on
Write-Host "已开启。修改发送时间/接收号请编辑 $PSScriptRoot\config.json" -ForegroundColor Green
