$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Python virtual environment not found at $venvPython. Run: py -m venv .venv"
    exit 1
}

Write-Host "Starting PhishGuard backend on http://127.0.0.1:8000"
& $venvPython -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
