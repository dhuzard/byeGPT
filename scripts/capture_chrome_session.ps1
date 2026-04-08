$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvDir = Join-Path $RepoRoot ".venv-backend"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    throw "Backend venv not found. Run .\scripts\start_host_backend.ps1 once first."
}

$env:BYEGPT_STORAGE = (Join-Path $RepoRoot ".byegpt")
& $PythonExe scripts/capture_chrome_session.py
