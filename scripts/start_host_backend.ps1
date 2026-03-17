$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvDir = Join-Path $RepoRoot ".venv-backend"

Set-Location $RepoRoot

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.11+ first."
}

if (-not (Test-Path $VenvDir)) {
    py -3 -m venv $VenvDir
}

$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r backend/requirements.txt
& $PythonExe -m playwright install chromium

$env:BYEGPT_STORAGE = (Join-Path $RepoRoot ".byegpt")
$env:BYEGPT_DEMO_MODE = "false"
$env:CORS_ORIGINS = "http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:3000,http://localhost:3000"

Write-Host "Host backend starting on http://127.0.0.1:8000"
Write-Host "Next step: open http://127.0.0.1:8000/docs or POST /auth/login to create .byegpt/storage.json"

& $PythonExe scripts/run_host_backend.py
