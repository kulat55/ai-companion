# 启动主动消息守护进程（后台常驻，开机后需要时手动运行一次即可）
$ROOT = Split-Path $PSScriptRoot -Parent
$py   = Join-Path $ROOT 'letta-server\venv\Scripts\python.exe'
$work = $PSScriptRoot
$pidf = Join-Path $work 'proactive.pid'
if (Test-Path $pidf) {
    $old = Get-Content $pidf -ErrorAction SilentlyContinue
    if ($old -and (Get-Process -Id $old -ErrorAction SilentlyContinue)) {
        Write-Host "守护进程已在运行 (PID $old)，无需重复启动。" -ForegroundColor Yellow
        return
    }
}
$p = Start-Process -FilePath $py -ArgumentList 'proactive_sender.py' -WorkingDirectory $work -WindowStyle Hidden -PassThru
$p.Id | Out-File -FilePath $pidf -Encoding ascii
Write-Host "主动消息守护进程已启动 (PID $($p.Id))。日志：$work\proactive.log" -ForegroundColor Green
Write-Host "注意：config.json 里 enabled 决定是否真的发送，可用 qq_on.ps1 / qq_off.ps1 切换。"
