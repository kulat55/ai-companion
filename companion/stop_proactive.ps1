# 停止主动消息守护进程
$pidf = 'D:\AICompanion\companion\proactive.pid'
if (Test-Path $pidf) {
    $procId = Get-Content $pidf -ErrorAction SilentlyContinue
    if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $procId -Force
        Write-Host "已停止守护进程 (PID $procId)。" -ForegroundColor Green
    } else { Write-Host "进程不在运行。" -ForegroundColor Yellow }
    Remove-Item $pidf -Force -ErrorAction SilentlyContinue
} else {
    # 兜底：按命令行匹配
    $hit = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
           Where-Object { $_.CommandLine -like '*proactive_sender.py*' }
    if ($hit) { $hit | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host "已停止 PID $($_.ProcessId)" } }
    else { Write-Host "没有找到守护进程。" -ForegroundColor Yellow }
}
