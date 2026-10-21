$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Python virtual environment not found at $venvPython. Run: py -m venv .venv"
    exit 1
}

Write-Host "Starting PhishGuard frontend on http://127.0.0.1:5502"
& $venvPython -m http.server 5502 --bind 127.0.0.1
