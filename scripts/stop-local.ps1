$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $projectRoot '.local-run\processes.json'
if (-not (Test-Path -LiteralPath $pidFile)) { Write-Host '没有本项目的启动记录。'; exit }
$processIds = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
foreach ($role in @('frontend','backend')) {
    $processId = $processIds.$role
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    if ($process -and $process.CommandLine -and $process.CommandLine.Contains($projectRoot)) {
        Stop-Process -Id $processId -ErrorAction SilentlyContinue
    }
}
Remove-Item -LiteralPath $pidFile
Write-Host '本地服务已停止。'
