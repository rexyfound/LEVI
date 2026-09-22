@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
title LEVI Kokoro Setup

where py >nul 2>nul
if errorlevel 1 goto :python_error

py -3.12 -c "import sys" >nul 2>nul
if errorlevel 1 (
    echo [LEVI] Python 3.12 is required for Kokoro and was not found.
    pause
    exit /b 1
)

set "KOKORO_RUNTIME=%CD%\backend\voice\.kokoro_runtime"
if not exist "%KOKORO_RUNTIME%\Scripts\python.exe" (
    echo [LEVI] Creating isolated Kokoro Python 3.12 runtime...
    py -3.12 -m venv "%KOKORO_RUNTIME%"
    if errorlevel 1 goto :failed
)

set "KOKORO_PYTHON=%KOKORO_RUNTIME%\Scripts\python.exe"
echo [LEVI] Installing Kokoro and its local neural dependencies...
"%KOKORO_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :failed
"%KOKORO_PYTHON%" -m pip install "kokoro==0.9.4" soundfile "misaki[en]"
if errorlevel 1 goto :failed
rem Use PyTorch's CUDA build instead of the CPU-only wheel published on PyPI.
"%KOKORO_PYTHON%" -m pip install --upgrade --force-reinstall "torch==2.8.0" --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 goto :failed

echo [LEVI] Verifying GPU access and downloading/loading the voice model once...
set "KOKORO_PYTHON=%KOKORO_PYTHON%"
"%KOKORO_PYTHON%" backend\voice\kokoro_worker.py < nul
if errorlevel 1 goto :failed

echo.
echo [LEVI] Kokoro is ready. Add these lines to .env:
echo TTS_PROVIDER=kokoro
echo TTS_VOICE=af_heart
echo KOKORO_SPEED=1.0
pause
exit /b 0

:python_error
echo [LEVI] Install Python 3.12 from python.org or Microsoft Store, then run this setup again.
pause
exit /b 1

:failed
echo [LEVI] Kokoro setup failed. LEVI will continue using Edge TTS.
pause
exit /b 1
