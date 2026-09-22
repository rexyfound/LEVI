@echo off
cd /d "%~dp0"
title LEVI AI Assistant

if not exist ".venv\Scripts\python.exe" (
    echo [LEVI] Setting up Python environment...
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo [LEVI] Starting LEVI...
.venv\Scripts\python.exe backend\ui.py
