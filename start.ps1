# File: start.ps1
# Description: PowerShell 1-click startup script for SwasthyaGrid AI (Backend + Frontend)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting SwasthyaGrid AI — District Health OS           " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$RootPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Start FastAPI Backend
Write-Host "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
$BackendProcess = Start-Process -FilePath "$RootPath\backend\.venv\Scripts\python.exe" -ArgumentList "$RootPath\backend\run_backend.py" -WorkingDirectory $RootPath -PassThru

Start-Sleep -Seconds 2

# 2. Start Vite Frontend
Write-Host "[2/2] Starting React Vite Frontend on http://localhost:3000..." -ForegroundColor Yellow
$FrontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -WorkingDirectory "$RootPath\frontend" -PassThru

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  SwasthyaGrid AI is Running Successfully!                " -ForegroundColor Green
Write-Host "  Web Dashboard:  http://localhost:3000                  " -ForegroundColor White
Write-Host "  FastAPI Docs:   http://127.0.0.1:8000/docs             " -ForegroundColor White
Write-Host "  RPC Endpoint:   http://127.0.0.1:8000/api/rpc/v1       " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C in this console or close the spawned windows to stop."

