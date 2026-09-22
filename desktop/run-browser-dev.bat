@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
  echo LEVI Python environment not found.
  echo Create it with: py -m venv .venv
  echo Then install dependencies with: .venv\Scripts\python.exe -m pip install -r requirements.txt
  pause
  exit /b 1
)

set LEVI_REPO_ROOT=%CD%
set LEVI_REPO_POLL_SECONDS=1.0

start "LEVI Backend" cmd /k "cd /d %CD%\backend && call ..\.venv\Scripts\activate && python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
start "LEVI Frontend" cmd /k "cd /d %CD%\frontend && npm install && npm run dev"

timeout /t 3 /nobreak >nul
start "" http://localhost:3000
