@echo off
rem File: start.bat
rem Description: Windows CMD Batch launcher for SwasthyaGrid AI

echo ==========================================================
echo   Starting SwasthyaGrid AI - District Health OS
echo ==========================================================

start "SwasthyaGrid Backend" cmd /k "backend\.venv\Scripts\python.exe backend\run_backend.py"
timeout /t 2 /nobreak >nul

start "SwasthyaGrid Frontend" cmd /k "cd frontend && npm run dev"

echo Backend running on http://127.0.0.1:8000
echo Frontend starting on http://localhost:3000
echo ==========================================================

