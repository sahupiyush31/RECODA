# DataFix Runner Script
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " DataFix --- Autonomous Data Quality & Repair Engine" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting DataFix at http://127.0.0.1:8000" -ForegroundColor Yellow

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptDir\backend"
$env:PYTHONPATH = (Get-Location).Path

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
