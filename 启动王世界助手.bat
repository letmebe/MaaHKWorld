@echo off
cd /d "%~dp0"

echo ========================================
echo   MaaHKWorld - Automation  Assistant
echo ========================================
echo.

REM Create desktop shortcut if not exists
set "SHORTCUT_NAME=MaaHKWorld.lnk"
set "SHORTCUT_PATH=%USERPROFILE%\Desktop\%SHORTCUT_NAME%"

if exist "%SHORTCUT_PATH%" goto :shortcut_done

echo [INFO] Creating desktop shortcut...

REM Detect icon path (development vs release)
set "ICON_PATH="
if exist "%~dp0assets\resource\image\logo.ico" (
    set "ICON_PATH=%~dp0assets\resource\image\logo.ico"
) else if exist "%~dp0resource\image\logo.ico" (
    set "ICON_PATH=%~dp0resource\image\logo.ico"
)

REM Use unique temp file name
set "PS_SCRIPT=%TEMP%\create_shortcut_%RANDOM%.ps1"

REM Create PowerShell script to create shortcut
(
    echo $WshShell = New-Object -ComObject WScript.Shell
    echo $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'^)
    echo $Shortcut.TargetPath = '%~f0'
    echo $Shortcut.WorkingDirectory = '%~dp0'
    echo $Shortcut.Description = 'MaaHKWorld - Automation Assistant'
    if not "%ICON_PATH%"=="" (
        echo $Shortcut.IconLocation = '%ICON_PATH%,0'
    )
    echo $Shortcut.Save(^)
) > "%PS_SCRIPT%"

REM Execute PowerShell script
powershell -ExecutionPolicy Bypass -File "%PS_SCRIPT%" >nul 2>&1

REM Delay then delete temp file
ping 127.0.0.1 -n 1 >nul 2>&1
del "%PS_SCRIPT%" >nul 2>&1

if exist "%SHORTCUT_PATH%" (
    echo [OK] Desktop shortcut created
) else (
    echo [WARNING] Failed to create desktop shortcut
)
echo.

:shortcut_done

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