# 查看雅儿贝德各组件运行状态
function Test-Port($p) {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $iar = $c.BeginConnect('127.0.0.1', $p, $null, $null)
    $ok = $iar.AsyncWaitHandle.WaitOne(700, $false)
    if ($ok) { $c.EndConnect($iar); $c.Close(); return $true }
    $c.Close(); return $false
  } catch { return $false }
}
function Row($name, $port) {
  if (Test-Port $port) { Write-Host ("[运行中] {0,-22} 端口 {1}" -f $name, $port) -ForegroundColor Green }
  else { Write-Host ("[未启动] {0,-22} 端口 {1}" -f $name, $port) -ForegroundColor Yellow }
}
Row 'Ollama 本地模型' 11434
$pgf = 'D:\AICompanion\pgdata\PORT'
if (Test-Path $pgf) { Row '内嵌数据库(PostgreSQL)' ((Get-Content $pgf).Trim()) }
else { Write-Host '[未启动] 内嵌数据库' -ForegroundColor Yellow }
Row 'Letta 记忆大脑' 8283
Row 'Live2D 桌宠' 12393

$cfg = Get-Content 'D:\AICompanion\companion\config.json' -Raw -Encoding UTF8 | ConvertFrom-Json
if ($cfg.enabled) { Write-Host '[已开启] QQ 主动消息开关' -ForegroundColor Green }
else { Write-Host '[已关闭] QQ 主动消息开关' -ForegroundColor Yellow }
$daemon = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*proactive_sender.py*' }
if ($daemon) { Write-Host '[运行中] QQ 主动消息守护进程' -ForegroundColor Green }
else { Write-Host '[未启动] QQ 主动消息守护进程' -ForegroundColor Yellow }
Write-Host "`n桌宠地址： http://localhost:12393   ；Letta 接口： http://localhost:8283"
