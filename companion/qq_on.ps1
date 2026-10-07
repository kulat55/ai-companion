# 开启“雅儿贝德主动发QQ”总开关（守护进程需已在运行；若没运行请先 start_proactive.ps1）
$py = 'D:\AICompanion\letta-server\venv\Scripts\python.exe'
& $py 'D:\AICompanion\companion\set_flag.py' on
Write-Host "已开启。修改发送时间/接收号请编辑 D:\AICompanion\companion\config.json" -ForegroundColor Green
