$ErrorActionPreference = "Stop"

$chromePaths = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
)

$chromeExe = $chromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $chromeExe) {
    throw "Chrome was not found. Install Google Chrome or update scripts/start_chrome_debug.ps1."
}

$DebugProfile = Join-Path $env:TEMP "byegpt-chrome-debug"

Write-Host "Starting Chrome with remote debugging on port 9222"
Write-Host "Using debug profile: $DebugProfile"

Start-Process -FilePath $chromeExe -ArgumentList @(
    "--remote-debugging-port=9222",
    "--user-data-dir=$DebugProfile",
    "https://notebooklm.google.com/"
)
