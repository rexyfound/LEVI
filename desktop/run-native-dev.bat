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

set LEVI_DESKTOP_DEV=1
set LEVI_REPO_ROOT=%CD%
set LEVI_REPO_POLL_SECONDS=1.0

cd desktop
if not exist "node_modules" (
  echo Installing desktop shell dependencies...
  call npm install
  if errorlevel 1 exit /b 1
)

call npm run dev
