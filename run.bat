@echo off
REM ============================================================
REM  SDG Policy Paper Agent - ONE-CLICK RUNNER (Windows)
REM  Just double-click this file, or type:  run.bat   in cmd
REM ============================================================
cd /d "%~dp0"

REM --- check Python is installed ---
where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found!
    echo Install it from https://www.python.org/downloads
    echo IMPORTANT: tick the box "Add python.exe to PATH" during install.
    echo.
    pause
    exit /b 1
)

REM --- create virtual environment once ---
if not exist .venv (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

REM --- install packages ---
echo [2/3] Installing/updating packages - may take a few minutes the first time...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Package installation failed. Check your internet and try again.
    pause
    exit /b 1
)

REM --- launch the app ---
echo [3/3] Starting the app - your browser will open at http://localhost:8501
echo.
streamlit run app.py

echo.
echo App stopped. Close this window or press any key to exit.
pause >nul
