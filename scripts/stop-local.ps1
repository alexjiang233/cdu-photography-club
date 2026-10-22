$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $projectRoot '.local-run\processes.json'
if (-not (Test-Path -LiteralPath $pidFile)) { Write-Host '没有本项目的启动记录。'; exit }
$processIds = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
foreach ($role in @('frontend','backend')) {
    $processId = $processIds.$role
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    if ($process -and $process.CommandLine -and $process.CommandLine.Contains($projectRoot)) {
        # Next and the Windows venv launcher create children; stop the whole owned tree.
        & taskkill.exe /PID $processId /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "无法停止本项目的 $role 进程树（PID $processId），请检查权限。" }
    }
}
Remove-Item -LiteralPath $pidFile
Write-Host '本地服务已停止。'
