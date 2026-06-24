@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ========================================
echo   MaaHKWorld - Automation Assistant
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

REM Create desktop shortcut if not exists
set "SHORTCUT_NAME=MaaHKWorld.lnk"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\%SHORTCUT_NAME%"

if not exist "%SHORTCUT_PATH%" (
    echo.
    echo [INFO] Creating desktop shortcut...
    python create_shortcut.py
)

echo.
echo [INFO] Configuring MFAAvalonia...

REM Check if development environment (assets/interface.json exists)
if exist "assets\interface.json" (
    REM Development: copy interface.json to tools/MFAAvalonia/
    if exist "tools\MFAAvalonia\MFAAvalonia.exe" (
        copy /Y "assets\interface.json" "tools\MFAAvalonia\interface.json" >nul
        echo [OK] Copied interface.json to tools/MFAAvalonia/
    )
)

echo [INFO] Starting MFAAvalonia...

REM Find MFAAvalonia.exe
REM Release package: current directory
REM Development: tools/MFAAvalonia/
set "MFA_EXE="
if exist "MFAAvalonia.exe" (
    set "MFA_EXE=MFAAvalonia.exe"
) else if exist "tools\MFAAvalonia\MFAAvalonia.exe" (
    set "MFA_EXE=tools\MFAAvalonia\MFAAvalonia.exe"
)

if "%MFA_EXE%"=="" (
    echo [ERROR] MFAAvalonia.exe not found
    pause
    exit /b 1
)

start "" "%MFA_EXE%"
