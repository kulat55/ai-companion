# 关闭AI 伴侣全部本地服务（桌宠程序 / backend 编排 / Letta / 内嵌数据库 / QQ守护）。
# 数据都在部署根目录，不会丢。
$ROOT = $PSScriptRoot

# 1) 先停 backend.py 编排进程：它一终止，Job Object 会自动回收它拉起的全部服务（最干净）
$backends = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like '*backend.py*' }
if ($backends) {
  $backends | ForEach-Object {
    try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop; Write-Host "已停止编排进程 backend (PID $($_.ProcessId))" -ForegroundColor Green } catch {}
  }
  Start-Sleep -Seconds 3
} else { Write-Host 'backend 编排进程未在运行' -ForegroundColor Yellow }

# 2) 若桌宠 exe（托盘程序）还在，一并关闭
$pet = Get-Process 'AI 伴侣桌宠' -ErrorAction SilentlyContinue
if ($pet) { $pet | Stop-Process -Force -ErrorAction SilentlyContinue; Write-Host '已关闭桌宠程序' -ForegroundColor Green }

# 3) 兜底：按命令行清理任何残留服务
function Stop-ByCmd($pattern, $name) {
  $hit = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
         Where-Object { $_.CommandLine -and ($_.CommandLine -like "*$pattern*") -and ($_.Name -ne 'powershell.exe') }
  if ($hit) {
    $hit | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} }
    Write-Host "已清理 $name" -ForegroundColor Green
  }
}
Stop-ByCmd 'run_server.py' '桌宠服务'
Stop-ByCmd 'letta' 'Letta 记忆服务'
Stop-ByCmd 'proactive_sender.py' 'QQ主动消息守护'
$pg = Get-CimInstance Win32_Process -Filter "Name='postgres.exe'" -ErrorAction SilentlyContinue |
      Where-Object { $_.CommandLine -like '*pgdata*' }
if ($pg) { $pg | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }; Write-Host '已清理内嵌数据库' -ForegroundColor Green }

# 4) 删除崩溃残留的 PG 锁，保证下次干净启动
Remove-Item (Join-Path $ROOT 'pgdata\postmaster.pid') -Force -ErrorAction SilentlyContinue
Write-Host '全部已关闭。' -ForegroundColor Cyan
