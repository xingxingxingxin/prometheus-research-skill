@echo off
REM Prometheus Research - 日志监控脚本 (Windows)

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set LOG_DIR=%SCRIPT_DIR%..\Logs

echo.
echo ========================================
echo   Prometheus Research 日志监控
echo ========================================
echo.

REM 查找最新的日志文件
for /f "delims=" %%f in ('dir /b /o-d "%LOG_DIR%\*.log" 2^>nul') do (
    set LATEST_LOG=%LOG_DIR%\%%f
    goto :found
)

echo 错误: 没有找到日志文件
echo.
echo 启动后台任务:
echo   scripts\run_background.bat
exit /b 1

:found
echo 日志文件: !LATEST_LOG!
echo.
echo 选择操作:
echo   1) 实时查看日志 (PowerShell)
echo   2) 查看最近 50 行
echo   3) 查看完整日志
echo   4) 搜索关键词
echo   5) 查看进度摘要
echo.
set /p choice="请选择 [1-5]: "

if "%choice%"=="1" (
    echo.
    echo 按 Ctrl+C 退出
    echo ----------------------------------------
    powershell -Command "Get-Content '!LATEST_LOG!' -Wait -Tail 50"
) else if "%choice%"=="2" (
    echo.
    echo ----------------------------------------
    powershell -Command "Get-Content '!LATEST_LOG!' -Tail 50"
) else if "%choice%"=="3" (
    echo.
    echo ----------------------------------------
    type "!LATEST_LOG!"
) else if "%choice%"=="4" (
    set /p keyword="输入搜索关键词: "
    echo.
    echo ----------------------------------------
    findstr /i "!keyword!" "!LATEST_LOG!"
) else if "%choice%"=="5" (
    echo.
    echo ----------------------------------------
    echo 进度摘要:
    echo.
    findstr /i "Phase 任务 TASK_COMPLETE ERROR WARNING" "!LATEST_LOG!" | more +0
) else (
    echo 无效选择
)

echo.
pause
