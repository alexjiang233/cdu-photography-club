param([switch]$Production)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) { throw '请先按 README 安装依赖。' }
foreach ($port in @(8000, 3000)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) { throw "端口 $port 已被占用，请先检查已有服务。" }
}
$runDir = Join-Path $projectRoot '.local-run'
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
Push-Location (Join-Path $projectRoot 'backend')
try {
    & $pythonExe manage.py migrate
    if ($LASTEXITCODE -ne 0) { throw '数据库迁移失败。' }
    & $pythonExe manage.py bootstrap_roles
    & $pythonExe manage.py collectstatic --noinput --verbosity 0
} finally { Pop-Location }
if ($Production) {
    Push-Location (Join-Path $projectRoot 'frontend')
    try { & npm.cmd run build; if ($LASTEXITCODE -ne 0) { throw '前端构建失败。' } } finally { Pop-Location }
}
$backendProcess = Start-Process -FilePath $pythonExe -ArgumentList @('manage.py','runserver','127.0.0.1:8000','--noreload') -WorkingDirectory (Join-Path $projectRoot 'backend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDir 'backend.log') -RedirectStandardError (Join-Path $runDir 'backend-error.log') -PassThru
$nodeExe = (Get-Command node.exe).Source
$nextCli = Join-Path $projectRoot 'frontend\node_modules\next\dist\bin\next'
$mode = if ($Production) { 'start' } else { 'dev' }
$frontendProcess = Start-Process -FilePath $nodeExe -ArgumentList @(('"{0}"' -f $nextCli),$mode,'--hostname','127.0.0.1') -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runDir 'frontend.log') -RedirectStandardError (Join-Path $runDir 'frontend-error.log') -PassThru
@{ backend = $backendProcess.Id; frontend = $frontendProcess.Id } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDir 'processes.json')
Write-Host '网站已启动：http://127.0.0.1:3000；管理后台：http://127.0.0.1:3000/admin/'
Write-Host '这是本地预览。正式部署请使用 docs/OPERATIONS.md。'
