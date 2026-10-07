# 关闭“雅儿贝德主动发QQ”总开关（即时生效，守护进程保留运行但不再发送）
$py = 'D:\AICompanion\letta-server\venv\Scripts\python.exe'
& $py 'D:\AICompanion\companion\set_flag.py' off
Write-Host "已关闭，雅儿贝德不会再主动发QQ。" -ForegroundColor Yellow
