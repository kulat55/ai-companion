# 关闭“AI 伴侣主动发QQ”总开关（即时生效，守护进程保留运行但不再发送）
$ROOT = Split-Path $PSScriptRoot -Parent
$py = Join-Path $ROOT 'letta-server\venv\Scripts\python.exe'
& $py (Join-Path $PSScriptRoot 'set_flag.py') off
Write-Host "已关闭，AI 伴侣不会再主动发QQ。" -ForegroundColor Yellow
