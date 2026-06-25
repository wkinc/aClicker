@echo off
title Auto Clicker Launcher

echo ==============================
echo   Auto Clicker Starting...
echo ==============================

:: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b
)

echo [OK] Python detected.

:: Check if requirements.txt exists
IF NOT EXIST requirements.txt (
    echo [ERROR] requirements.txt not found!
    pause
    exit /b
)

:: Install dependencies
echo Installing dependencies (if needed)...
pip install -r requirements.txt

:: Check if main.py exists
IF NOT EXIST main.py (
    echo [ERROR] main.py not found!
    pause
    exit /b
)

:: Run the app
echo Launching Auto Clicker...
python main.py

pause