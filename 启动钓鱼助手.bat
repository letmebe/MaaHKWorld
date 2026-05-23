@echo off
cd /d "%~dp0"

echo ========================================
echo   MaaHKWorld - Auto Fishing Assistant
echo ========================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check virtual environment
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Check dependencies
venv\Scripts\python.exe -c "import maafw, vgamepad, win32api, cv2, numpy" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    echo This may take a few minutes...
    venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
)

echo.
echo [INFO] Starting MFAAvalonia...
start "" "MFAAvalonia.exe"
