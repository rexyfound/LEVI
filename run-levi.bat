@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem Always run relative to this checkout, even when launched from a shortcut.
cd /d "%~dp0"
set "LEVI_ROOT=%CD%"
title LEVI Desktop

rem Prefer the Windows Python launcher, but support installations that expose
rem only python.exe on PATH.
where py >nul 2>nul
if not errorlevel 1 (
    set "LEVI_BOOTSTRAP_PY=py -3"
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [LEVI] Python 3.11 or newer was not found.
        echo [LEVI] Install Python, then run this launcher again.
        pause
        exit /b 1
    )
    set "LEVI_BOOTSTRAP_PY=python"
)

if not exist ".venv\Scripts\python.exe" (
    echo [LEVI] Creating the local Python environment...
    %LEVI_BOOTSTRAP_PY% -m venv .venv
    if errorlevel 1 goto :python_error
)

set "LEVI_PYTHON=%LEVI_ROOT%\.venv\Scripts\python.exe"
set "LEVI_REPO_ROOT=%LEVI_ROOT%"
set "LEVI_REPO_POLL_SECONDS=1.0"
set "LEVI_DATA_DIR=%LOCALAPPDATA%\LEVI\data"
set "PYTHONUTF8=1"

if not exist "%LEVI_DATA_DIR%" mkdir "%LEVI_DATA_DIR%" >nul 2>nul

set "LEVI_INSTALL_PY=0"
if not exist ".venv\.levi_dependencies_ready" set "LEVI_INSTALL_PY=1"
if "%LEVI_INSTALL_PY%"=="1" (
    echo [LEVI] Installing Python dependencies...
    "%LEVI_PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 goto :dependency_error
    "%LEVI_PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 goto :dependency_error
    type nul > ".venv\.levi_dependencies_ready"
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [LEVI] Node.js and npm are required for the desktop interface.
    echo [LEVI] Install the current Node.js LTS release, then run this launcher again.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [LEVI] Installing frontend dependencies...
    call npm --prefix frontend install
    if errorlevel 1 goto :dependency_error
)

rem The desktop launcher starts FastAPI, Vite, and Electron as one lifecycle.
call desktop\run-native-dev.bat
set "LEVI_EXIT_CODE=%ERRORLEVEL%"
if not "%LEVI_EXIT_CODE%"=="0" (
    echo.
    echo [LEVI] Desktop launcher stopped with error code %LEVI_EXIT_CODE%.
    pause
)
exit /b %LEVI_EXIT_CODE%

:python_error
echo [LEVI] Could not create the virtual environment.
echo [LEVI] Confirm that Python 3.11 or newer is installed and accessible.
pause
exit /b 1

:dependency_error
echo [LEVI] Dependency installation failed. Check your internet connection and retry.
pause
exit /b 1
