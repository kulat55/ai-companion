# ============================================================
# AI 伴侣 AI 伴侣 · 一键启动（脚本方式）
# 直接交给经过完整可靠性加固的 backend.py：
#   数据库(55432) -> Letta 记忆大脑(8283) -> Live2D 桌宠(12393) 全自动
# powershell -ExecutionPolicy Bypass -File start_all.ps1
#
# 说明：本窗口开着 = 桌宠在运行；关闭本窗口 / Ctrl+C = 自动停止全部后台服务。
#       想要托盘后台常驻、开机自启，请直接双击桌面的「AI 伴侣桌宠」程序（推荐）。
# ============================================================
$ROOT    = 'D:\AICompanion'
$PY      = Join-Path $ROOT 'desktop\venv\Scripts\python.exe'
$BACKEND = Join-Path $ROOT 'desktop\backend.py'

# 让 backend 以本窗口为“父”：窗口关闭时父看门自动清理全部服务（Job Object 兜底，零孤儿）
$env:PARENT_PID = $PID
$env:PYTHONIOENCODING = 'utf-8'

Write-Host '正在按顺序启动：数据库(55432) -> Letta 记忆大脑(8283) -> Live2D 桌宠(12393) ...' -ForegroundColor Cyan
Write-Host '首次启动约需 1-2 分钟（Live2D 加载语音和人格最慢），请耐心等待，勿关闭窗口。' -ForegroundColor Yellow
Write-Host '启动后若想用浏览器界面，手动打开 http://localhost:12393 。' -ForegroundColor DarkGray
Write-Host ''

& $PY $BACKEND

Write-Host "`n后台服务已停止。" -ForegroundColor Yellow
