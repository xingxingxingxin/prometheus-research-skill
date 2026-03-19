@echo off
REM Prometheus Research - 快速启动脚本 (Windows)
REM 用法: quick_start.bat "研究主题"

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set TOPIC=%~1

echo.
echo ========================================
echo   Prometheus Research - 快速启动
echo ========================================
echo.

if "%TOPIC%"=="" (
    set /p TOPIC="请输入研究主题: "
)

if "%TOPIC%"=="" (
    echo 错误: 研究主题不能为空
    exit /b 1
)

echo 研究主题: %TOPIC%
echo.
echo 正在初始化项目...
echo.

REM 启动研究
python "%SCRIPT_DIR%start_research.py" --topic "%TOPIC%"

if errorlevel 1 (
    echo.
    echo 错误: 项目初始化失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo   项目初始化完成!
echo ========================================
echo.
echo 后续操作:
echo.
echo   1. 后台执行任务:
echo      call scripts\run_background.bat
echo.
echo   2. 查看进度:
echo      call scripts\monitor.bat
echo.
echo   3. 查看状态:
echo      python scripts\prometheus.py --status
echo.
pause
