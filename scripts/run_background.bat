@echo off
REM Prometheus Research - 后台执行脚本 (Windows)

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set LOG_DIR=%SCRIPT_DIR%..\Logs
set PROJECTS_DIR=%SCRIPT_DIR%..\Projects

REM 创建日志目录
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM 生成日志文件名
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
set LOG_FILE=%LOG_DIR%\executor_%TIMESTAMP%.log

echo.
echo ========================================
echo   Prometheus Research 后台执行
echo ========================================
echo.

REM 检查是否有项目
if "%~1"=="" (
    REM 查找最新的项目
    for /f "delims=" %%d in ('dir /b /ad /o-d "%PROJECTS_DIR%" 2^>nul') do (
        set LATEST_PROJECT=%%d
        goto :found
    )
    echo 错误: 没有找到项目
    echo 请先启动一个研究:
    echo   python scripts/start_research.py --topic "研究主题"
    exit /b 1
    :found
    set PROJECT=%PROJECTS_DIR%\!LATEST_PROJECT!
    echo 使用最新项目: !LATEST_PROJECT!
) else (
    set PROJECT=%PROJECTS_DIR%\%~1
    if not exist "!PROJECT!" (
        echo 错误: 项目不存在: %~1
        exit /b 1
    )
)

echo.
echo 日志文件: %LOG_FILE%
echo 项目目录: %PROJECT%
echo.
echo ----------------------------------------
echo   后台执行中... 查看进度命令:
echo.
echo   # PowerShell 实时日志
echo   Get-Content "%LOG_FILE%" -Wait -Tail 50
echo.
echo   # 或用记事本打开
echo   notepad "%LOG_FILE%"
echo ----------------------------------------
echo.

REM 后台执行
start /b pythonw "%SCRIPT_DIR%automation\task_executor.py" --project "%PROJECT%" --loop >> "%LOG_FILE%" 2>&1

echo 已启动后台任务
echo.
echo 监控命令:
echo   查看日志: Get-Content "%LOG_FILE%" -Wait -Tail 50
echo   查看状态: python scripts/prometheus.py --status
echo.
pause
