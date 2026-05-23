@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   MaaHKWorld - 王者荣耀世界自动钓鱼助手
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查虚拟环境是否存在
if not exist "venv\Scripts\python.exe" (
    echo [信息] 虚拟环境不存在，正在创建...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [成功] 虚拟环境创建完成
)

REM 检查依赖是否已安装
venv\Scripts\python.exe -c "import maafw, vgamepad, win32api" >nul 2>&1
if errorlevel 1 (
    echo [信息] 依赖未安装，正在安装...
    echo 这可能需要几分钟，请耐心等待...
    venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [成功] 依赖安装完成
)

echo.
echo [信息] 启动 MFAAvalonia...
start "" "MFAAvalonia.exe"
